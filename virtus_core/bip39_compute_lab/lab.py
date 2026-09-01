"""
BIP39 COMPUTE LAB — technological hypothesis from compute videos.

ALLOWED:
  - generate / validate BIP-39 vectors (synthetic / own)
  - derive address fingerprints for throughput bench
  - multi-worker batch processing
  - read-only public chain checks for OWN addresses

FORBIDDEN (hard reject — never implement execution path):
  - brute-force / search foreign mnemonics
  - sweep third-party wallets
  - treat “found funded foreign seed” as FOUND income

FOUND (income) requires:
  address + tx/blockchain proof + confirmed balance
  + legal source + transferability
  — NEVER “a number on screen” from model hashing rate.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "bip39_compute_lab"
_LAST = _RUNTIME / "last_bench.json"

# Tiny subset of BIP39 English for validation bench (full list not required for throughput demo)
_BIP39_SAMPLE = (
    "abandon ability able about above absent absorb abstract absurd abuse access accident "
    "account accuse achieve acid acoustic acquire across act action actor actress actual "
    "adapt add addict address adjust admit adult advance advice aerobic affair afford afraid "
    "again age agent agree ahead aim air airport aisle alarm album alcohol alert alien all "
    "alley allow almost alone alpha already also alter always amateur amazing among amount "
    "amused analyst anchor ancient anger angle angry animal ankle announce annual another "
    "answer antenna antique anxiety any anybody anyone anything apart apology appear apple "
    "approve april arch arctic area arena argue arm armed armor army around arrange arrest "
    "arrive arrow art artefact artist artwork ask aspect assault asset assist assume asthma "
    "athlete atom attack attend attitude attract auction audit august aunt author auto autumn "
    "average avocado avoid awake aware away awesome awful awkward axis baby bachelor bacon "
    "badge bag balance balcony ball bamboo banana banner bar barely bargain barrel base basic "
    "basket battle beach bean beauty because become beef before begin behave behind believe "
    "below belt bench benefit best betray better between beyond bicycle bid bike bind biology "
    "bird birth bitter black blade blame blanket blast bleak bless blind blood blossom blouse "
    "blue blur blush board boat body boil bomb bone bonus book boost border boring borrow boss "
    "bottom bounce box boy bracket brain brand brass brave bread breeze brick bridge brief "
    "bright bring brisk broccoli broken bronze broom brother brown brush bubble buddy budget "
    "buffalo build bulb bulk bullet bundle bunker burden burger burst bus business busy butter "
    "buyer buzz cabbage cabin cable cactus cage cake call calm camera camp can canal cancel "
    "candy cannon canoe canvas canyon capable capital captain car carbon card cargo carpet "
    "carry cart case cash casino castle casual cat catalog catch category cattle caught cause "
    "caution cave ceiling celery cement census century cereal certain chair chalk champion "
    "change chaos chapter charge chase chat cheap check cheese chef cherry chest chicken chief "
    "child chimney choice choose chronic chuckle chunk churn cigar cinnamon circle citizen city "
    "civil claim clap clarify claw clay clean clerk clever click client cliff climb clinic clip "
    "clock clog close cloth cloud clown club clump cluster clutch coach coast coconut code coffee "
    "coil coin collect color column combine come comfort comic common company concert conduct "
    "confirm congress connect consider control convince cook cool copper copy coral core corn "
    "correct cost cotton couch country couple course cousin cover coyote crack cradle craft cram "
    "crane crash crater crawl crazy cream credit creek crew cricket crime crisp critic crop cross "
    "crouch crowd crucial cruel cruise crumble crunch crush cry crystal cube culture cup cupboard "
    "curious current curtain curve cushion custom cute cycle dad damage damp dance danger daring "
    "dash daughter dawn day deal debate debris decade december decide decline decorate decrease "
    "deer defense define defy degree delay deliver demand demise denial dentist deny depart depend "
    "deposit depth deputy derive describe desert design desk despair destroy detail detect develop "
    "device devote diagram dial diamond diary dice diesel diet differ digital dignity dilemma dinner "
    "dinosaur direct dirt disagree discover disease dish dismiss disorder display distance divert "
    "divide divorce dizzy doctor document dog doll dolphin domain donate donkey donor door dose "
    "double dove draft dragon drama drastic draw dream dress drift drill drink drip drive drop "
    "drum dry duck dumb dune during dust dutch duty dwarf dynamic eager eagle early earn earth "
    "easily east easy echo ecology economy edge edit educate effort egg eight either elbow elder "
    "electric elegant element elephant elevator elite else embark embody embrace emerge emotion "
    "employ empower empty enable enact end endless endorse enemy energy enforce engage engine "
    "enhance enjoy enlist enough enrich enroll ensure enter entire entry envelope episode equal "
    "equip era erase erode erosion error erupt escape essay essence estate eternal ethics even "
    "event every everyday evidence evil evoke evolve exact example excess exchange excite exclude "
    "excuse execute exercise exhaust exhibit exile exist exit exotic expand expect expire explain "
    "expose express extend extra eye eyebrow fabric face faculty fade faint faith fall false fame "
    "family famous fan fancy fantasy farm fashion fat fatal father fatigue fault favorite feature "
    "february federal fee feed feel female fence festival fetch fever few fiber fiction field "
    "figure file film filter final find fine finger finish fire firm first fiscal fish fit "
    "fitness fix flag flame flash flat flavor flee flight flip float flock floor flower fluid "
    "flush fly foam focus fog foil fold follow food foot force forest forget fork fortune forum "
    "forward fossil foster found fox fragile frame frequent fresh friend fringe frog front frost "
    "frown frozen fruit fuel fun funny furnace fury future gadget gain galaxy gallery game gap "
    "garage garbage garden garlic garment gas gasp gate gather gauge gaze general genius genre "
    "gentle genuine gesture ghost giant gift giggle ginger giraffe girl give glad glance glare "
    "glass glide glimpse globe gloom glory glove glow glue goat goddess gold good goose gorilla "
    "gospel gossip govern gown grab grace grain grant grape grass gravity great green grid grief "
    "grit grocery group grow grunt guard guess guide guilt guitar gun gym habit hair half hammer "
    "hamster hand happy harbor hard harsh harvest hat have hawk hazard head health hear heart "
    "heavy hedgehog height hello helmet help hen hero hidden high hill hint hip hire history "
    "hobby hockey hold hole holiday hollow home honey hood hope horn horror horse hospital host "
    "hotel hour hover hub huge human humble humor hundred hungry hunt hurdle hurry hurt husband "
    "hybrid ice icon idea identify idle ignore ill illegal illness image imitate immense immune "
    "impact impose improve impulse inch include income increase index indicate indoor industry "
    "infant inflict inform inhale inherit initial inject injury inmate inner innocent input "
    "inquiry insane insect inside inspire install intact interest into invest invite involve iron "
    "island isolate issue item ivory jacket jaguar jar jazz jealous jeans jelly jewel job join "
    "joke journey joy judge juice jump jungle junior junk just kangaroo keen keep ketchup key "
    "kick kid kidney kind kingdom kiss kit kitchen kite kitten kiwi knee knife knock know lab "
    "label labor ladder lady lake lamp language laptop large later latin laugh laundry lava law "
    "lawn lawsuit layer lazy leader leaf learn leave lecture left leg legal legend leisure lemon "
    "lend length lens leopard lesson letter level liar liberty library license life lift light "
    "like limb limit link lion liquid list little live lizard load loan lobster local lock logic "
    "lonely long loop lottery loud lounge love loyal lucky luggage lumber lunar lunch luxury "
    "lyrics machine mad magic magnet maid mail main major make mammal man manage mandate mango "
    "mansion manual maple marble march margin marine market marriage mask mass master match "
    "material math matrix matter maximum maze meadow mean measure meat mechanic medal media "
    "melody melt member memory mention menu mercy merge merit merry mesh message metal method "
    "middle midnight milk million mimic mind minimum minor minute miracle mirror misery miss "
    "mistake mix mixed mixture mobile model modify mom moment monitor monkey monster month moon "
    "moral more morning mosquito mother motion motor mountain mouse move movie much muffin mule "
    "multiply muscle museum mushroom music must mutual myself mystery myth naive name napkin "
    "narrow nasty nation nature near neck need negative neglect neither nephew nerve nest net "
    "network neutral never news next nice night noble noise nominee noodle noon north nose "
    "notable note nothing notice novel now nuclear number nurse nut oak obey object oblige "
    "obscure observe obtain obvious occur ocean october odor off offer office often oil okay "
    "old olive olympic omit once one onion online only open opera opinion oppose option orange "
    "orbit orchard order ordinary organ orient original orphan ostrich other outdoor outer "
    "output outside oval oven over own owner oxygen oyster ozone pact paddle page pair palace "
    "palm panda panel panic panther paper parade parent park parrot party pass patch path "
    "patient patrol pattern pause pave payment peace peanut pear peasant pelican pen penalty "
    "pencil people pepper perfect permit person pet phone photo phrase physical piano picnic "
    "picture piece pig pigeon pill pilot pink pioneer pipe pistol pitch pizza place planet "
    "plastic plate play please pledge pluck plug plunge poem poet point polar pole police pond "
    "pony pool popular portion position possible post potato pottery poverty powder power "
    "practice praise predict prefer prepare present pretty prevent price pride primary print "
    "priority prison private prize problem process produce profit program project promote proof "
    "property prosper protect proud provide public pudding pull pulp pulse pumpkin punch pupil "
    "puppy purchase purity purpose purse push put puzzle pyramid quality quantum quarter "
    "question quick quit quiz quote rabbit raccoon race rack radar radio rail rain raise rally "
    "ramp ranch random range rapid rare rate rather raven raw razor ready real reason rebel "
    "rebuild recall receive recipe record recycle reduce reflect reform refuse region regret "
    "regular reject relax release relief rely remain remember remind remove render renew rent "
    "reopen repair repeat replace report require rescue resemble resist resource response result "
    "retire retreat return reunion reveal review reward rhythm rib ribbon rice rich ride ridge "
    "rifle right rigid ring riot ripple risk ritual rival river road roast robot robust rocket "
    "romance roof rookie room rose rotate rough round route royal rubber rude rug rule run "
    "runway rural sad saddle sadness safe sail salad salmon salon salt salute same sample sand "
    "satisfy satoshi sauce sausage save say scale scan scare scatter scene scheme school science "
    "scissors scorpion scout scrap screen script scrub sea search season seat second secret "
    "section security seed seek segment select sell seminar senior sense sentence series "
    "service session settle setup seven shadow shaft shallow share shed shell sheriff shield "
    "shift shine ship shiver shock shoe shoot shop short shoulder shove shrimp shrug shuffle "
    "shy sibling sick side siege sight sign silent silk silly silver similar simple since sing "
    "siren sister situate six size skate sketch ski skill skin skirt skull slab slam sleep "
    "slender slice slide slight slim slogan slot slow slush small smart smile smoke smooth snack "
    "snake snap sniff snow soap soccer social sock soda soft solar soldier solid solution solve "
    "someone song soon sorry sort soul sound soup source south space spare spatial spawn speak "
    "special speed spell spend sphere spice spider spike spin spirit split spoil sponsor spoon "
    "sport spot spray spread spring spy square squeeze squirrel stable stadium staff stage "
    "stairs stamp stand start state stay steak steel stem step stereo stick still sting stock "
    "stomach stone stool story stove strategy street strike strong struggle student stuff "
    "stumble style subject submit subway success such sudden suffer sugar suggest suit summer "
    "sun sunny sunset super supply supreme sure surface surge surprise surround survey suspect "
    "sustain swallow swamp swap swarm swear sweet swift swim swing switch sword symbol symptom "
    "syrup system table tackle tag tail talent talk tank tape target task taste tattoo taxi "
    "teach team tell ten tenant tennis tent term test text thank that theme then theory there "
    "they thing this thought three thrive throw thumb thunder ticket tide tiger tilt timber "
    "time tiny tip tired tissue title toast tobacco today toddler toe together toilet token "
    "tomato tomorrow tone tongue tonight tool tooth top topic topple torch tornado tortoise "
    "toss total tourist toward tower town toy track trade traffic tragic train transfer trap "
    "trash travel tray treat tree trend trial tribe trick trigger trim trip trophy trouble "
    "truck true truly trumpet trust truth try tube tuition tumble tuna tunnel turkey turn "
    "turtle twelve twenty twice twin twist two type typical ugly umbrella unable unaware uncle "
    "uncover under undo unfair unfold unhappy uniform unique unit universe unknown unlock "
    "until unusual unveil update upgrade uphold upon upper upset urban urge usage use used "
    "useful useless usual utility vacant vacuum vague valid valley valve van vanish vapor "
    "various vast vault vehicle velvet vendor venture venue verb verify version very vessel "
    "veteran viable vibrant vicious victory video view village vintage violin virtual virus "
    "visa visit visual vital vivid vocal voice void volcano volume vote voyage wage wagon wait "
    "walk wall walnut want warfare warm warrior wash wasp waste water wave way wealth weapon "
    "wear weasel weather web wedding weekend weird welcome west wet whale what wheat wheel when "
    "where whip whisper wide width wife wild will win window wine wing wink winner winter wire "
    "wisdom wise wish witness wolf woman wonder wood wool word work world worry worth wrap "
    "wreck wrestle wrist write wrong yard year yellow you young youth zebra zero zone zoo"
).split()

_WORDSET = frozenset(_BIP39_SAMPLE)

SECURITY_REJECTED_PATHS = (
    "foreign_mnemonic_bruteforce",
    "third_party_wallet_sweep",
    "seed_search_for_funded_wallets",
    "video_claim_as_income_without_proof",
)

FOUND_CRITERIA = (
    "address",
    "tx_or_blockchain_proof",
    "confirmed_balance",
    "legal_source",
    "transferability",
)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def reject_foreign_seed_path(idea: str = "") -> dict[str, Any]:
    return {
        "status": "SECURITY_REJECTED",
        "reason": "BIP39 lab must not hunt foreign secrets / funded third-party wallets",
        "idea_class": idea or "foreign_seed_search",
        "lesson": "Compute capacity ≠ income. Video hashrate claims ≠ FOUND.",
        "forbidden": list(SECURITY_REJECTED_PATHS),
    }


def _synthetic_mnemonic(n_words: int = 12) -> list[str]:
    return [secrets.choice(_BIP39_SAMPLE) for _ in range(n_words)]


def _validate_words(words: list[str]) -> bool:
    return all(w in _WORDSET for w in words) and len(words) in (12, 15, 18, 21, 24)


def _derive_fingerprint(words: list[str], account: int = 0) -> str:
    """Throughput stand-in for HD derivation — not a production wallet path."""
    material = (" ".join(words) + f"|acct={account}").encode("utf-8")
    seed = hashlib.pbkdf2_hmac("sha512", material, b"mnemonic" + b"virtus-lab", 2048, dklen=64)
    return hashlib.sha256(seed).hexdigest()[:40]


def _worker_batch(batch_size: int) -> dict[str, Any]:
    t0 = time.perf_counter()
    ok = 0
    fps: list[str] = []
    for _ in range(batch_size):
        w = _synthetic_mnemonic(12)
        if _validate_words(w):
            ok += 1
            fps.append(_derive_fingerprint(w))
    dt = max(time.perf_counter() - t0, 1e-9)
    return {"ok": ok, "seconds": dt, "vectors_per_sec": ok / dt, "sample_fp": fps[:2]}


def run_bip39_bench(*, workers: int = 8, batch_per_worker: int = 200, max_workers: int = 64) -> dict[str, Any]:
    workers = max(1, min(int(workers), max_workers))
    batch_per_worker = max(10, int(batch_per_worker))
    t0 = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_worker_batch, batch_per_worker) for _ in range(workers)]
        for f in as_completed(futs):
            results.append(f.result())
    total_ok = sum(r["ok"] for r in results)
    elapsed = max(time.perf_counter() - t0, 1e-9)
    return {
        "module": "BIP39_COMPUTE_LAB",
        "at": _now(),
        "workers": workers,
        "batch_per_worker": batch_per_worker,
        "total_vectors": total_ok,
        "elapsed_sec": round(elapsed, 4),
        "vectors_per_sec": round(total_ok / elapsed, 2),
        "mode": "SYNTHETIC_OWN_ONLY",
        "telegram_required": False,
        "income_claimed": False,
        "law": "Throughput metrics ≠ REAL money. Foreign seed search = SECURITY_REJECTED.",
        "security": reject_foreign_seed_path("video_style_wallet_finder"),
    }


def evaluate_found_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Iron FOUND criteria — screen number alone fails."""
    missing = [k for k in FOUND_CRITERIA if not candidate.get(k)]
    if candidate.get("source_class") in SECURITY_REJECTED_PATHS or candidate.get("foreign_seed"):
        return {
            "found": False,
            "status": "SECURITY_REJECTED",
            "missing": FOUND_CRITERIA,
            "reason": "illegal_or_forbidden_source",
        }
    if missing:
        return {"found": False, "status": "NOT_FOUND", "missing": missing, "reason": "incomplete_proof"}
    if not candidate.get("confirmed_balance") or float(candidate.get("confirmed_balance") or 0) <= 0:
        return {"found": False, "status": "NOT_FOUND", "missing": ["confirmed_balance>0"], "reason": "no_balance"}
    return {
        "found": True,
        "status": "FOUND",
        "missing": [],
        "proof": {k: candidate.get(k) for k in FOUND_CRITERIA},
    }


def public_chain_analyzer(*, own_addresses: list[str] | None = None, offline: bool = False) -> dict[str, Any]:
    """Read-only public chain probes — OWN addresses only. No Telegram."""
    addrs = [a.strip() for a in (own_addresses or []) if a and a.strip()]
    # Default: genesis admin from state if present (own)
    state_path = _ROOT / ".runtime" / "vcore_genesis_state.json"
    if not addrs and state_path.exists():
        try:
            g = json.loads(state_path.read_text(encoding="utf-8"))
            if g.get("adminAddress"):
                addrs.append(str(g["adminAddress"]))
        except Exception:
            pass

    events: list[dict[str, Any]] = []
    if offline or not addrs:
        return {
            "at": _now(),
            "module": "PUBLIC_CHAIN_ANALYZER",
            "telegram_required": False,
            "addresses_checked": addrs,
            "events": [],
            "note": "offline or no own addresses — analyzer idle",
            "status": "IDLE" if not addrs else "OFFLINE",
        }

    import urllib.parse
    import urllib.request

    for addr in addrs[:5]:
        try:
            url = f"https://testnet.tonapi.io/v2/accounts/{urllib.parse.quote(addr)}"
            req = urllib.request.Request(url, headers={"User-Agent": "VirtusBip39Lab/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                j = json.loads(r.read().decode("utf-8"))
            bal = float(j.get("balance") or 0) / 1e9
            events.append(
                {
                    "network": "ton-testnet",
                    "address": addr,
                    "balance_ton": bal,
                    "account_status": j.get("status"),
                    "own": True,
                    "legal_source": "OWN_WALLET_READ",
                }
            )
        except Exception as e:
            events.append({"address": addr, "error": str(e), "own": True})

    return {
        "at": _now(),
        "module": "PUBLIC_CHAIN_ANALYZER",
        "telegram_required": False,
        "addresses_checked": addrs,
        "events": events,
        "status": "OK",
        "note": "Public events on OWN addresses only — not foreign seed hunting",
    }


def opportunity_ai_bridge(*, offline: bool = False) -> dict[str, Any]:
    """Second agent: systematic economic discovery (compute-first)."""
    try:
        from virtus_core.opportunity_ai.systematic import systematic_discover

        # Bench already measured in dual path — do not nest vectors/s as income.
        sysd = systematic_discover(offline=offline, measure_compute=False)
        return {
            "module": "OPPORTUNITY_AI",
            "source": "systematic_economic_discovery",
            "epoch_status": sysd.get("epoch_status"),
            "outcome": sysd.get("scientific_result"),
            "message": sysd.get("message"),
            "counts": sysd.get("counts"),
            "priority_order": sysd.get("priority_order"),
            "top_compute_first": sysd.get("top_compute_first"),
            "path": "CPU → verifiable work → protocol reward → REAL → converter → Treasury",
            "forbidden": "BIP39 foreign wallet finder · force-confirm hypothesis",
            "honest_negative": "NO_VALID_OPPORTUNITY",
        }
    except Exception as e:
        return {
            "module": "OPPORTUNITY_AI",
            "error": str(e),
            "epoch_status": "NO_VALID_OPPORTUNITY",
            "outcome": "HONEST_NEGATIVE",
            "honest_negative": "NO_VALID_OPPORTUNITY",
        }


def run_dual_architecture(*, workers: int = 8, batch: int = 150, offline: bool = False) -> dict[str, Any]:
    """
              VIRTUS
                 │
        ┌────────┴────────┐
        ↓                 ↓
 BIP39 COMPUTE LAB   PUBLIC CHAIN ANALYZER
        │                 │
        └────────┬────────┘
                 ↓
          OPPORTUNITY AI
                 ↓
       TESTNET/OWN | LEGIT REWARDS → TREASURY
    """
    bench = run_bip39_bench(workers=workers, batch_per_worker=batch)
    chain = public_chain_analyzer(offline=offline)
    opp = opportunity_ai_bridge(offline=offline)

    # Explicit: video-style “earnings” are NOT FOUND
    fake_found = evaluate_found_candidate(
        {
            "address": None,
            "tx_or_blockchain_proof": None,
            "confirmed_balance": bench["vectors_per_sec"],  # screen number trap
            "legal_source": None,
            "transferability": None,
            "foreign_seed": False,
        }
    )

    report = {
        "engine": "Virtus Dual Compute Architecture",
        "version": "1.0.0",
        "at": _now(),
        "telegram_required": False,
        "insight": (
            "Video shows interesting compute ideas, but does NOT prove claimed earnings. "
            "We reuse the compute architecture; we reject foreign-seed income paths."
        ),
        "bip39_compute_lab": bench,
        "public_chain_analyzer": chain,
        "opportunity_ai": opp,
        "found_criteria": list(FOUND_CRITERIA),
        "screen_number_is_not_found": fake_found,
        "treasury_handoff": {
            "allowed_when": "FOUND = address + tx proof + confirmed balance + legal source + transferable",
            "real_external_assets": 0,
            "painted_from_hashrate": False,
        },
        "security_policy_immutable": list(SECURITY_REJECTED_PATHS) + ["ai_must_not_read_owner_mnemonic"],
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _LAST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
