data "azurerm_client_config" "current" {}

data "azurerm_user_assigned_identity" "main" {
  count               = var.tde_enabled_create == true ? 1 : 0
  name                = local.user_identity_name
  resource_group_name = local.user_identity_resource_group
}
resource "azurerm_mssql_server" "main" {
  name                                         = var.name
  resource_group_name                          = var.resource_group
  location                                     = var.location
  version                                      = "12.0"
  administrator_login                          = var.administrator_login != "" ? var.administrator_login : null
  administrator_login_password                 = var.administrator_login_password != "" ? var.administrator_login_password : null
  minimum_tls_version                          = "1.2"
  transparent_data_encryption_key_vault_key_id = var.tde_enabled_create == true ? azurerm_key_vault_key.main[0].id : var.transparent_data_encryption_key_vault_key_id != "" ? var.transparent_data_encryption_key_vault_key_id : null
  primary_user_assigned_identity_id            = var.primary_user_assigned_identity_id != "" ? var.primary_user_assigned_identity_id : null
  dynamic "azuread_administrator" {
    for_each = var.object_id == "" ? toset([]) : toset([1])
    content {
      login_username              = var.ad_admin
      object_id                   = var.object_id
      azuread_authentication_only = true
    }

  }

  dynamic "identity" {
    for_each = var.primary_user_assigned_identity_id == "" ? toset([]) : toset([1])
    content {
      type         = "UserAssigned"
      identity_ids = [var.primary_user_assigned_identity_id]
    }

  }
  tags = {
    managed = "rc"
  }
}

resource "azurerm_mssql_server_dns_alias" "main" {
  name            = var.dns_alias
  mssql_server_id = azurerm_mssql_server.main.id
}

resource "azurerm_mssql_virtual_network_rule" "main" {
  name      = "${var.name}-rule"
  server_id = azurerm_mssql_server.main.id
  subnet_id = var.subnet_id
}

resource "azurerm_mssql_firewall_rule" "main" {
  count            = var.start_ip_address == "" || var.end_ip_address == "" ? 0 : 1
  name             = "${var.name}-fw-rule"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = var.start_ip_address
  end_ip_address   = var.end_ip_address
}

resource "azurerm_key_vault" "main" {
  count                       = var.tde_enabled_create == true ? 1 : 0
  name                        = "mssqlrcvault${random_integer.ri.result}"
  location                    = var.location
  resource_group_name         = var.resource_group
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = true

  sku_name = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = ["Get", "List", "Create", "Delete", "Update", "Recover", "Purge", "GetRotationPolicy"]
  }

  access_policy {
    tenant_id = data.azurerm_user_assigned_identity.main[0].tenant_id
    object_id = data.azurerm_user_assigned_identity.main[0].principal_id

    key_permissions = ["Get", "WrapKey", "UnwrapKey"]
  }
}

resource "azurerm_key_vault_key" "main" {
  count      = var.tde_enabled_create == true ? 1 : 0
  depends_on = [azurerm_key_vault.main]

  name         = "sql-key"
  key_vault_id = azurerm_key_vault.main[count.index].id
  key_type     = "RSA"
  key_size     = 2048

  key_opts = ["unwrapKey", "wrapKey"]
}

resource "random_integer" "ri" {
  min = 10000
  max = 99999
}
