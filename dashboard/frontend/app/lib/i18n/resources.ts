import deChat from "../../../locales/de/chat.json";
import deCommon from "../../../locales/de/common.json";
import deErrors from "../../../locales/de/errors.json";
import deSite from "../../../locales/de/site.json";
import enChat from "../../../locales/en/chat.json";
import enCommon from "../../../locales/en/common.json";
import enErrors from "../../../locales/en/errors.json";
import enSite from "../../../locales/en/site.json";
import ruChat from "../../../locales/ru/chat.json";
import ruCommon from "../../../locales/ru/common.json";
import ruErrors from "../../../locales/ru/errors.json";
import ruSite from "../../../locales/ru/site.json";
import { LOCALE_REGISTRY } from "../locale/registry";

type LocaleBundle = Record<string, object>;

const translatedBundles: Record<string, LocaleBundle> = {
  ru: { common: ruCommon, chat: ruChat, site: ruSite, errors: ruErrors },
  en: { common: enCommon, chat: enChat, site: enSite, errors: enErrors },
  de: { common: deCommon, chat: deChat, site: deSite, errors: deErrors },
};

const englishFallback = translatedBundles.en;

/** i18n resources for every platform locale — untranslated locales use English bundles. */
export const localeResources: Record<string, LocaleBundle> = Object.fromEntries(
  LOCALE_REGISTRY.map((def) => [def.code, translatedBundles[def.code] ?? englishFallback]),
);
