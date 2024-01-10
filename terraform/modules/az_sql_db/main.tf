resource "azurerm_mssql_database" "main" {
  name           = var.name
  server_id      = var.server_id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  license_type   = "LicenseIncluded"
  max_size_gb    = var.max_size_gb
  read_scale     = false
  sku_name       = "S1"
  zone_redundant = false

  tags = {
    managed = "rc"
  }
}

resource "azurerm_mssql_firewall_rule" "main" {
  count            = var.start_ip_address == "" || var.end_ip_address == "" ? 0 : 1
  name             = "${var.name}-fw-rule"
  server_id        = var.server_id
  start_ip_address = var.start_ip_address
  end_ip_address   = var.end_ip_address
}

