# Producers

- Fields :

  - x_off_org_id
  - x_off_main_contact
  - x_off_last_import_date
  - x_off_last_export_date

- Inherited view:

  - res.partner :
    - button to open org in pro platform (when partner is 'company')
    - new custom off fields, see ir_model_fields.yml

- Automated action:

  - [email] new org welcome (sends an email to the org main contact)

- Email templates:

  - New org - welcome

- Server Action:

  - Open in pro plateform as org (res.partner)

- Tags (crm.tag):
  - onboarding

[Dasel](https://github.com/TomWright/dasel) was used to transform Odoo csv exports into yaml :

```sh
cat data.csv | dasel -r csv -w yaml
```
