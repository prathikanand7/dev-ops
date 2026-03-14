variable "lifewatch_key_name" {
  description = "Name of the API Gateway API key."
  type        = string
}

variable "api_id" {
  description = "ID of the REST API. Use the api_gateway module's api_id output."
  type        = string
}

variable "stage_name" {
  description = "Name of the API Gateway stage to attach the usage plan to."
  type        = string
}

variable "usage_plan_name" {
  description = "Name of the usage plan."
  type        = string
}

variable "usage_plan_description" {
  description = "Description of the usage plan."
  type        = string
  default     = ""
}

variable "burst_limit" {
  description = "Maximum request burst size (concurrent requests above rate_limit)."
  type        = number
  default     = 5
}

variable "rate_limit" {
  description = "Steady-state request rate limit (requests per second)."
  type        = number
  default     = 10
}
