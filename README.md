# odoo-openfoodfacts

Some odoo related stuff that we use at openfoodfacts.

It would be great to transform that into a real module.

## Looking for Odoo volunteers
* We need volunteers to maintain and expand our on-prem install of Odoo.
* Feel free to ping us on Slack or at contact@openfoodfacts.org


## Copying a change

Right now to copy changes from the platform,
I use the "export" action and then use `yq` to transform the csv into yaml.

`yq -p "csv" -oy exported.csv > exported.yaml`
