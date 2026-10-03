export interface HealthResponse {
  status: string
  environment: string
  project_name: string
}

export type ProductUnit = 'UN' | 'KG' | 'G' | 'L' | 'ML'

export interface ProductInput {
  name: string
  base_unit: ProductUnit
}

export interface Product extends ProductInput {
  id: number
  active: boolean
  inventory_balance: string
  created_at: string
  updated_at: string
}

export interface InventoryMovement {
  id: number
  product_id: number
  quantity: string
  type: 'ENTRY' | 'ADJUSTMENT'
  created_at: string
}
