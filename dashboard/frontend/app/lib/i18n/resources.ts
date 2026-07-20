import deChat from "../../../locales/de/chat.json";
import deCommon from "../../../locales/de/common.json";
import deErrors from "../../../locales/de/errors.json";
import deSite from "../../../locales/de/site.json";
import enChat from "../../../locales/en/chat.json";
import enCommon from "../../../locales/en/common.json";
import enErrors from "../../../locales/en/errors.json";
import enSite from "../../../locales/en/site.json";
import csChat from "../../../locales/cs/chat.json";
import csCommon from "../../../locales/cs/common.json";
import csErrors from "../../../locales/cs/errors.json";
import csSite from "../../../locales/cs/site.json";
import esChat from "../../../locales/es/chat.json";
import esCommon from "../../../locales/es/common.json";
import esErrors from "../../../locales/es/errors.json";
import esSite from "../../../locales/es/site.json";
import frChat from "../../../locales/fr/chat.json";
import frCommon from "../../../locales/fr/common.json";
import frErrors from "../../../locales/fr/errors.json";
import frSite from "../../../locales/fr/site.json";
import itChat from "../../../locales/it/chat.json";
import itCommon from "../../../locales/it/common.json";
import itErrors from "../../../locales/it/errors.json";
import itSite from "../../../locales/it/site.json";
import nlChat from "../../../locales/nl/chat.json";
import nlCommon from "../../../locales/nl/common.json";
import nlErrors from "../../../locales/nl/errors.json";
import nlSite from "../../../locales/nl/site.json";
import plChat from "../../../locales/pl/chat.json";
import plCommon from "../../../locales/pl/common.json";
import plErrors from "../../../locales/pl/errors.json";
import plSite from "../../../locales/pl/site.json";
import ptChat from "../../../locales/pt/chat.json";
import ptCommon from "../../../locales/pt/common.json";
import ptErrors from "../../../locales/pt/errors.json";
import ptSite from "../../../locales/pt/site.json";
import ruChat from "../../../locales/ru/chat.json";
import ruCommon from "../../../locales/ru/common.json";
import ruErrors from "../../../locales/ru/errors.json";
import ruSite from "../../../locales/ru/site.json";
import ukChat from "../../../locales/uk/chat.json";
import ukCommon from "../../../locales/uk/common.json";
import ukErrors from "../../../locales/uk/errors.json";
import ukSite from "../../../locales/uk/site.json";
import { LOCALE_REGISTRY } from "../locale/registry";

type LocaleBundle = Record<string, object>;

const translatedBundles: Record<string, LocaleBundle> = {
  ru: { common: ruCommon, chat: ruChat, site: ruSite, errors: ruErrors },
  en: { common: enCommon, chat: enChat, site: enSite, errors: enErrors },
  de: { common: deCommon, chat: deChat, site: deSite, errors: deErrors },
  uk: { common: ukCommon, chat: ukChat, site: ukSite, errors: ukErrors },
  cs: { common: csCommon, chat: csChat, site: csSite, errors: csErrors },
  es: { common: esCommon, chat: esChat, site: esSite, errors: esErrors },
  fr: { common: frCommon, chat: frChat, site: frSite, errors: frErrors },
  it: { common: itCommon, chat: itChat, site: itSite, errors: itErrors },
  nl: { common: nlCommon, chat: nlChat, site: nlSite, errors: nlErrors },
  pl: { common: plCommon, chat: plChat, site: plSite, errors: plErrors },
  pt: { common: ptCommon, chat: ptChat, site: ptSite, errors: ptErrors },
};

const englishFallback = translatedBundles.en;

/** i18n resources for every platform locale — untranslated locales use English bundles. */
export const localeResources: Record<string, LocaleBundle> = Object.fromEntries(
  LOCALE_REGISTRY.map((def) => [def.code, translatedBundles[def.code] ?? englishFallback]),
);
