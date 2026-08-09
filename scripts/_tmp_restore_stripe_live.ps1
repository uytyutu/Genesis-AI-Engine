# Restore Stripe LIVE on Railway service renewed-reprieve (beta)
# NO SECRETS in this file — pull values from Railway Variable History / CEO dashboard.
#
# BEFORE-STATE (2026-07-28, prior to temporary test QA):
#   STRIPE_SECRET_KEY        = sk_live***   (was live)
#   STRIPE_PUBLISHABLE_KEY   = pk_live***   (was live)
#   STRIPE_WEBHOOK_SECRET    = whsec***     (unchanged during test QA)
#   STRIPE_SECRET_KEY_LIVE   = NOT SET on renewed-reprieve (did not exist)
#   GENESIS_STRIPE_SMOKE     = present (leave as-is)
#
# AFTER TEST QA (current until restore):
#   STRIPE_SECRET_KEY        = sk_test***
#   STRIPE_PUBLISHABLE_KEY   = pk_test***
#   STRIPE_WEBHOOK_SECRET    = unchanged
#
# NOTE: `railway variables --set "STRIPE_SECRET_KEY_LIVE="` FAILS (invalid empty format).
#       LIVE override was not present; no delete needed for restore unless you added it later.
#
# Project: adventurous-youth | Env: production | Service: renewed-reprieve
# Linked: railway link -p adventurous-youth -s renewed-reprieve -e production

Write-Host "=== Stripe LIVE restore steps (renewed-reprieve / beta) ==="
Write-Host ""
Write-Host "1) Open Railway Dashboard -> project adventurous-youth -> service renewed-reprieve -> Variables"
Write-Host "2) Restore from Variable History (or CEO password manager):"
Write-Host "     STRIPE_SECRET_KEY      <- previous sk_live_... value"
Write-Host "     STRIPE_PUBLISHABLE_KEY <- previous pk_live_... value"
Write-Host "3) Do NOT set STRIPE_SECRET_KEY_LIVE unless you intentionally use dual-key override."
Write-Host "   If STRIPE_SECRET_KEY_LIVE exists with sk_live while primary is sk_test, LIVE WINS in app code."
Write-Host "4) Leave STRIPE_WEBHOOK_SECRET as-is unless you also rotated webhook secrets."
Write-Host "5) Wait ~90-120s for redeploy, then verify:"
Write-Host '     Invoke-RestMethod https://beta.genesis-ai-engine.com/api/sales/payment-status'
Write-Host "   Expect: live_mode=true, provider_label containing live (not test)."
Write-Host ""
Write-Host "Optional CLI (paste LIVE values yourself; do not commit them):"
Write-Host '  railway variables --set "STRIPE_SECRET_KEY=<sk_live_from_history>" --set "STRIPE_PUBLISHABLE_KEY=<pk_live_from_history>" --service renewed-reprieve --environment production'
Write-Host ""
Write-Host "Never echo full Stripe secrets to stdout/logs."
