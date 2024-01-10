locals {
  key_vault       = var.key_vault_key_id != "" ? split("|", var.key_vault_key_id)[0] : null
  key             = var.key_vault_key_id != "" ? split("|", var.key_vault_key_id)[1] : null
  is_userassigned = length(regexall("UserAssigned", var.identity_type)) > 0
}
