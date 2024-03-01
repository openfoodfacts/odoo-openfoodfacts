TRANSLATE_ATTR = {"tooltip", "legend", "html", "label"}

if record:
  records = [record]
elif records:
  records = list(records)

def batch(l, n):
  results = []
  result = []
  for e in l:
    result.append(e)
    if len(result) >= n:
      results.append(result)
      result = []
  if result:
    results.append(result)
  return results

VALID_KEY_CHARS = set("0123456789abcdefghijklmnopqrstuvwxyz")

def value_to_key(value, default):
  # we can't use codecs module :'(
  last = None
  chars = ["off_"]
  for c in value.lower():
    if c in VALID_KEY_CHARS:
      chars.append(c)
      last = c
    elif last != "_":
      chars.append("_")
      last = "_"
  return "".join(chars[:100]).strip("_")

def get_translations(elt, prefix=""):
  """Parse the form structure to get all translatable fields"""
  translations = []
  sub_elt = []
  if isinstance(elt, list):
      sub_elt = list(enumerate(elt))
  elif isinstance(elt, dict):
      for attr in TRANSLATE_ATTR:
          value = elt.get(attr)
          if value:
              translations.append((value_to_key(value, ("%s_%s" % (prefix, attr)).lstrip("_")), value))
      sub_elt = list(elt.items())
  for name, e in sub_elt:
      translations.extend(get_translations(e, prefix="%s_%s" % (prefix, name)))
  return translations

def get_known_translations():
  countries = env["ir.translation"].search([("name", "=" , "res.country,name"), ("lang", "=", "fr_FR")])
  return {c.src: c.value for c in countries}


french_id = env["res.lang"].search([("code", "=", "fr_FR")], limit=1).ids[0]
builder_id = record.id
known_translations = get_known_translations()

for record in records:
  jsform = json.loads(record["schema"])
  all_translations = list(get_translations(jsform))
  for translations in batch(all_translations, 100):
    translations = dict(translations)
    # update existing
    existing = env["formio.builder.translation"].search([("lang_id", "=", french_id), ("source", "in", list(translations.values()))])
    # create missing
    missing = set(translations.keys()) - set(e.source for e in existing)
    env["formio.builder.translation"].create([
      {
        "builder_id": builder_id,
        "source": translations[prop],
        "lang_id": french_id,
        "value": known_translations.get(translations[prop], translations[prop] + " (en)")
      }
      for prop in missing
    ])