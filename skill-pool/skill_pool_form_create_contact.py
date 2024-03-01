# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - model: Odoo Model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: Odoo function to compare floats based on specific precisions
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - UserError: Warning Exception to use with raise
#  - Command: x2Many commands namespace
# To return an action, assign: action = {...}
# log("New Skill pool submission")
try:
  # TEST !!! to test with url
  if record is None:
      raise RuntimeError("Skill pool form: no record provided")  
      log("Creating from form 9 via web")
      record = env["formio.form"].browse([9])[0]
  # fields that directly map from the form data to odoo field
  contact_fields = {
    "email": "email",
    "website": "linkedin",
    "name": "name",
    "x_off_slack_id": "slackId",
    "x_off_username": "offUsername",
    "lang": "language",
    "x_off_languages": "languages",
    "country_id": "country",
    "city": "city",
    "function": "jobPosition",
  }
  # select format(' "%s": %s,', lower(name), id) from crm_tag where name ilike 'team %' or name ilike 'volunteer' or name ilike '%ly';
  crm_tags = {
      "daily": 36,
      "weekly": 37,
      "monthly": 38,
      "yearly": 39,
      "volunteer": 40,
      "team communication": 41,
      "team database": 42,
      "team events": 43,
      "team fundraising": 44,
      "team going global": 45,
      "team tech": 46,
      "team partnerships": 47,
  }
  # select format(' "%s": %s,', lower(name), id) from res_partner_category where name ilike 'team %' or name ilike 'volunteer' or name ilike '%ly';
  partner_tags = {
      "monthly": 169,
      "yearly": 171,
      "volunteer": 102,
      "daily": 167,
      "weekly": 170,
      "team database": 255,
      "team events": 266,
      "team fundraising": 271,
      "team tech": 217,
      "team going global": 131,
      "team partnerships": 123,
      "team communication": 330,
  }
  # fields to put in internal notes: label, field_name
  internal_notes_fields = [
    ("Interest", "interest"),
    ("Motivation", "motivation"),
    ("Other Orgs", "otherOrgsDesc"),
    ("Primary Skills", "primarySkill"),
    ("Secondary Skills", "secondarySkill"),
    ("Comments", "comments"),
  ]
  # team to place lead into
  community_team_id = 7;
  # stage id for lead
  skill_pool_stage_id = 27;
  # team leaders
  # Those are users id, not partner ids, find them in settings / manage users
  team_leaders = {
    "team database": 2, # Charles 
    "team communication": 14, # Gala
    "team events": 14, # Gala
    "team fundraising": 2, # Charles
    "team going global": 11,  # Pierre
    "team tech": 13, # Alex
    "team partnerships": 8, # Manon
    # mixed teams
    None: 14, # Gala
  }
  default_data = {
    "company_type": "person",
    # "author_id": 2,  # odoo bot
  }

  # loading data
  form_data = json.loads(record.submission_data)
  
  # creating partner data
  partner_data = dict(**default_data)
  for field, form_key in contact_fields.items():
    if form_key in form_data and str(form_data[form_key]).lower() not in ("", "none", "[]", "{}"):
      partner_data[field] = form_data[form_key]
  # some specific transformations #
  # country is a link to a table
  if partner_data.get("country_id"):
    # it's a dict with label and value
    country_id = partner_data["country_id"]["value"]
    countries = env["res.country"].search([("code", "=", country_id.upper())], limit=1)
    partner_data["country_id"] = countries[0].id
  # communication language
  if partner_data.get("lang"):
    languages = env["res.lang"].search([("code", "=", partner_data["lang"])], limit=1)
    partner_data["lang"] = languages[0].code  # we have to use code
  # spoken languages
  if partner_data.get("x_off_languages"):
    langs = [lang for lang in partner_data["x_off_languages"]]
    langs = env["res.lang"].search([("iso_code", "in", langs), ("active", "in", (True, False))], limit=len(langs))
    partner_data["x_off_languages"] = [Command.set(langs.ids)]
    # as string
    partner_data["x_off_languages_str"] = ", ".join(sorted(lang.name.split("/", 1)[0] for lang in langs))
  # Tags
  contact_tags = ["volunteer"]
  if form_data.get("frequency"):
    contact_tags.append(form_data["frequency"].lower())
  if form_data.get("main_team"):
    main_team = form_data["main_team"].lower()
    contact_tags.append(main_team)
  else:
    main_team = None
  if form_data.get("teams"):
    contact_tags.extend(k.lower() for k, v in form_data["teams"].items() if v and k.lower() != main_team)
  # get ids and remove eventual None values
  contact_tag_ids = list(filter(lambda x: x, (partner_tags.get(tag) for tag in contact_tags)))
  # remove the one that may not exists
  contact_tag_ids = env["res.partner.category"].browse(contact_tag_ids).ids
  partner_data["category_id"] = [Command.set(contact_tag_ids)]

  notes = []
  for title, form_key in internal_notes_fields:
    value = form_data.get(form_key, None)
    if value:
      notes.append("<p><b>%s:</b></p>" % title)
      notes.append("<p>%s</p>" % value.replace("\n", "<br>"))
  partner_data["comment"] = "<p></p>".join(notes)
  
  partner = env['res.partner'].create(partner_data)
  
  # create welcome lead
  lead_data = {
    "partner_id": partner.id,
    "country_id": partner.country_id.id,
    "name": "Welcome %s" % partner.name,
    "description": partner.comment,
    "stage_id": skill_pool_stage_id,
  }
  lead_tag_ids = [crm_tags[tag] for tag in contact_tags]
  # keep only existing
  lead_tag_ids = env["crm.tag"].browse(lead_tag_ids).ids
  lead_data["tag_ids"] = [Command.set(lead_tag_ids)]
  # add to community team
  lead_data["team_id"] = community_team_id
  # compute lead owner
  if main_team:
    leaders = [team_leaders.get(main_team)]
  else:
    leaders = set(team_leaders.get(tag) for tag in contact_tags) - {None}
  if len(leaders) == 1:
    lead_data['user_id'] = list(leaders)[0]
  else:
    lead_data['user_id'] = team_leaders[None]
  # create
  opportunity = env['crm.lead'].create(lead_data)

  # an automated email will be sent by sent by another automated action
except Exception as e:
  log("Skill pool form: Got exception %s while processing form %s" % (e, record.id), level='error')
