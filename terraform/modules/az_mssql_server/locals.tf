locals {
  user_identity_name           = var.primary_user_assigned_identity_id != "" ? split("/", var.primary_user_assigned_identity_id)[8] : null
  user_identity_resource_group = var.primary_user_assigned_identity_id != "" ? split("/", var.primary_user_assigned_identity_id)[4] : null
}
