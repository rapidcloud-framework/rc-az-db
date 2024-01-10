variable "name" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group" {
  type = string
}

variable "administrator_login" {
  type    = string
  default = null
}

variable "administrator_login_password" {
  type    = string
  default = null
}

variable "dns_alias" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "start_ip_address" {
  type = string
}

variable "end_ip_address" {
  type = string
}

variable "ad_admin" {
  type    = string
  default = ""
}

variable "object_id" {
  type    = string
  default = ""
}

variable "primary_user_assigned_identity_id" {
  type    = string
  default = ""
}

variable "transparent_data_encryption_key_vault_key_id" {
  type    = string
  default = ""
}

variable "tde_enabled_create" {
  type    = bool
  default = false
}
