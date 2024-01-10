data "azurerm_key_vault_key" "main" {
  count        = var.key_vault_key_id != "" ? 1 : 0
  name         = local.key
  key_vault_id = local.key_vault
}

resource "azurerm_cosmosdb_sql_database" "main" {
  count               = var.database_name != "" ? 1 : 0
  name                = var.database_name
  resource_group_name = var.resource_group
  account_name        = azurerm_cosmosdb_account.main.name
  throughput          = var.total_throughput_limit
}

resource "azurerm_cosmosdb_sql_container" "main" {
  for_each              = { for container in var.containers : container.container_name => container if var.database_name != "" }
  name                  = each.value.container_name
  resource_group_name   = var.resource_group
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.main[0].name
  partition_key_path    = each.value.partition_key
  partition_key_version = 1
  unique_key {
    paths = [each.value.unique_key]
  }
}

resource "azurerm_cosmosdb_account" "main" {
  name                              = var.name
  location                          = var.location
  resource_group_name               = var.resource_group
  offer_type                        = "Standard"
  enable_free_tier                  = var.enable_free_tier
  enable_multiple_write_locations   = var.enable_multiple_write_locations
  is_virtual_network_filter_enabled = var.subnet_id != "" ? true : false
  key_vault_key_id                  = var.key_vault_key_id != "" ? data.azurerm_key_vault_key.main[0].versionless_id : null
  enable_automatic_failover         = true
  ip_range_filter                   = var.ip_range_filter != "" ? var.ip_range_filter : null
  dynamic "capabilities" {
    for_each = var.enable_serverless == false ? toset([]) : toset([1])

    content {
      name = "EnableServerless"
    }
  }

  dynamic "geo_location" {
    for_each = length(var.geo_location) < 1 ? toset([]) : var.geo_location
    iterator = item

    content {
      location          = item.value
      failover_priority = index(var.geo_location, item.value) == 0 ? 0 : index(var.geo_location, item.value)
    }
  }

  consistency_policy {
    consistency_level = "Session"
  }

  capacity {
    total_throughput_limit = var.total_throughput_limit
  }

  dynamic "virtual_network_rule" {
    for_each = var.subnet_id == "" ? toset([]) : toset([1])

    content {
      id = var.subnet_id
    }
  }

  dynamic "backup" {
    for_each = var.backup_type == "" ? toset([]) : toset([1])

    content {
      type                = var.backup_type
      interval_in_minutes = var.backup_type == "Periodic" ? var.interval_in_minutes : null
      retention_in_hours  = var.backup_type == "Periodic" ? var.retention_in_hours : null
      storage_redundancy  = var.backup_type == "Periodic" ? var.storage_redundancy : null
    }
  }

  dynamic "identity" {
    for_each = var.identity_type == "" ? toset([]) : toset([1])
    content {
      type         = var.identity_type
      identity_ids = local.is_userassigned ? var.identity_ids : null
    }

  }

}
