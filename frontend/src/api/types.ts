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

export interface CompositionItem {
  product_id: number
  product_name: string
  product_active: boolean
  base_unit: ProductUnit
  quantity: string
  inventory_balance: string
  stock_available: boolean
  stock_shortage: string
}

export interface BasketTemplate {
  id: number
  name: string
  active: boolean
  created_at: string
  updated_at: string
  items: CompositionItem[]
}

export interface Basket {
  id: number
  name: string
  template_id: number | null
  created_at: string
  updated_at: string
  items: CompositionItem[]
}

export interface CompositionInput {
  product_id: number
  quantity: string
}
