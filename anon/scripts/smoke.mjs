/**
 * Local smoke: register A → create anon → sandbox pay →
 * register B → open free → reply free → ask_reveal pay →
 * assert identity not leaked.
 * Requires: npm run dev on :3100 and ANON_PAYMENT_SANDBOX=1
 */
const BASE = process.env.ANON_PUBLIC_URL || "http://localhost:3100";

function jar() {
  const cookies = new Map();
  return {
    store(res) {
      const raw = res.headers.getSetCookie?.() || [];
      for (const c of raw) {
        const [pair] = c.split(";");
        const i = pair.indexOf("=");
        if (i > 0) cookies.set(pair.slice(0, i), pair.slice(i + 1));
      }
    },
    header() {
      return [...cookies.entries()].map(([k, v]) => `${k}=${v}`).join("; ");
    },
    clear() {
      cookies.clear();
    },
  };
}

async function register(c, label) {
  const email = `smoke_${label}_${Date.now()}@anon.test`;
  const r = await fetch(`${BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password: "smoke-pass-123",
      displayName: label === "A" ? "SenderSmoke" : "RecipientSmoke",
      language: "en",
    }),
  });
  c.store(r);
  if (!r.ok) throw new Error(`register ${label} ${r.status} ${await r.text()}`);
  return email;
}

async function main() {
  const a = jar();
  const emailA = await register(a, "A");

  let r = await fetch(`${BASE}/api/gifts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: a.header(),
    },
    body: JSON.stringify({
      type: "SEND_ANON",
      message: "Smoke secret for reply economy",
      anonymous: true,
      theme: "mystery",
    }),
  });
  a.store(r);
  const created = await r.json();
  if (!r.ok) throw new Error(`gift ${JSON.stringify(created)}`);

  r = await fetch(`${BASE}/api/payments/checkout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: a.header(),
    },
    body: JSON.stringify({ orderId: created.orderId }),
  });
  const pay = await r.json();
  if (!r.ok) throw new Error(`pay ${JSON.stringify(pay)}`);

  const token = created.gift.token;
  const giftId = created.gift.id;

  // Recipient B — open free (no second payment)
  const b = jar();
  const emailB = await register(b, "B");

  r = await fetch(`${BASE}/api/gifts/open/${token}`);
  const openGet = await r.json();
  if (!r.ok) throw new Error(`open get ${JSON.stringify(openGet)}`);
  if (openGet.paidBySender !== true) throw new Error("expected paidBySender");
  if (openGet.gift?.revealedName) throw new Error("identity leaked on open GET");
  if (openGet.gift?.revealStatus === "revealed") {
    throw new Error("already revealed before ask");
  }

  r = await fetch(`${BASE}/api/gifts/open/${token}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: b.header(),
    },
    body: JSON.stringify({ action: "open" }),
  });
  if (!r.ok) throw new Error(`open post ${await r.text()}`);

  r = await fetch(`${BASE}/api/gifts/open/${token}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: b.header(),
    },
    body: JSON.stringify({ action: "reply", message: "thanks — free reply" }),
  });
  const reply = await r.json();
  if (!r.ok) throw new Error(`reply ${JSON.stringify(reply)}`);

  // Paid ask_reveal — request only, must not leak identity
  r = await fetch(`${BASE}/api/gifts/${giftId}/engage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: b.header(),
    },
    body: JSON.stringify({ action: "ask_reveal" }),
  });
  const engageOrder = await r.json();
  if (!r.ok) throw new Error(`ask_reveal ${JSON.stringify(engageOrder)}`);
  if (engageOrder.sku !== "ASK_REVEAL") throw new Error("wrong sku");

  r = await fetch(`${BASE}/api/payments/checkout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: b.header(),
    },
    body: JSON.stringify({ orderId: engageOrder.orderId }),
  });
  const engagePay = await r.json();
  if (!r.ok) throw new Error(`engage pay ${JSON.stringify(engagePay)}`);

  r = await fetch(`${BASE}/api/gifts/open/${token}`);
  const afterAsk = await r.json();
  if (!r.ok) throw new Error(`open after ask ${JSON.stringify(afterAsk)}`);
  if (afterAsk.gift?.revealedName) {
    throw new Error("ask_reveal leaked revealedName");
  }
  if (afterAsk.gift?.revealStatus === "revealed") {
    throw new Error("ask_reveal auto-revealed identity");
  }
  if (afterAsk.gift?.engage?.revealRequest !== "pending") {
    throw new Error(`expected reveal pending, got ${afterAsk.gift?.engage?.revealRequest}`);
  }

  // Sender A sees request — still no real name in engage payload
  r = await fetch(`${BASE}/api/gifts/${giftId}/engage`, {
    headers: { Cookie: a.header() },
  });
  const senderView = await r.json();
  if (!r.ok) throw new Error(`sender engage ${JSON.stringify(senderView)}`);
  if (senderView.role !== "sender") throw new Error("sender role");
  if (senderView.engage?.revealRequest !== "pending") {
    throw new Error("sender missing pending reveal");
  }
  const blob = JSON.stringify(senderView);
  if (blob.includes(emailA) || blob.includes("SenderSmoke")) {
    // display name must not appear as leaked identity field on engage status
    if (blob.includes('"revealedName"') || blob.includes("SenderSmoke")) {
      throw new Error("sender engage leaked identity fields");
    }
  }

  r = await fetch(`${BASE}/api/gifts/${giftId}/engage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: a.header(),
    },
    body: JSON.stringify({ action: "decline_reveal" }),
  });
  const declined = await r.json();
  if (!r.ok) throw new Error(`decline ${JSON.stringify(declined)}`);

  r = await fetch(`${BASE}/api/gifts/open/${token}`);
  const finalOpen = await r.json();
  if (finalOpen.gift?.revealedName || finalOpen.gift?.revealStatus === "revealed") {
    throw new Error("identity leaked after decline");
  }

  console.log("SMOKE PASS", {
    emailA,
    emailB,
    giftId,
    token,
    threadId: reply.threadId,
    sandbox: pay.sandbox ?? true,
    engageSandbox: engagePay.sandbox ?? true,
    revealRequest: finalOpen.gift?.engage?.revealRequest,
  });
}

main().catch((e) => {
  console.error("SMOKE FAIL", e.message || e);
  process.exit(1);
});
