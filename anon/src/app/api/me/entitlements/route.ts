import { getSessionUser } from "@/lib/auth";
import { json } from "@/lib/api";
import {
  botLimitForUser,
  canUseHardBots,
  FREE_BOT_LIMIT,
  listEntitlements,
  PREMIUM_BOT_LIMIT,
} from "@/lib/entitlements";

export async function GET() {
  const user = await getSessionUser();
  if (!user) {
    return json({
      loggedIn: false,
      entitlements: [],
      botLimit: FREE_BOT_LIMIT,
      hardBots: false,
      premiumBotLimit: PREMIUM_BOT_LIMIT,
    });
  }
  return json({
    loggedIn: true,
    entitlements: await listEntitlements(user.id),
    botLimit: await botLimitForUser(user.id),
    hardBots: await canUseHardBots(user.id),
    premiumBotLimit: PREMIUM_BOT_LIMIT,
  });
}
