# Current Task: Add Integration Monitoring APIs

## Task Description

Add two new integration monitoring APIs to the juspay_dashboard_mcp project based on provided curl examples:

1. **Platform-based Product Integration Query** - Groups by platform, returns product integration data
2. **Product Count by Integration Type Query** - Groups by product_integrated, returns product count metrics

## Context

These APIs are used in the ReScript Euler Dashboard UI for:
* Platform dropdown population and tab creation
* Product selection logic and dynamic product arrays
* Integration health calculation and completion percentages

## Implementation Plan

### Phase 1: Add New API Functions

* [x] Add `get_integration_platform_metrics_juspay` function for platform-based queries
* [x] Add `get_integration_product_count_metrics_juspay` function for product count queries
* [x] Ensure proper payload structure matching curl examples
* [x] Handle different groupBy parameters and filters

### Phase 2: Update Schema Definitions

* [x] Create `JuspayIntegrationPlatformMetricsPayload` schema class
* [x] Create `JuspayIntegrationProductCountMetricsPayload` schema class
* [x] Add proper field validation and descriptions
* [x] Include optional fields like debug, source, innerSelect, secondInnerSelect

### Phase 3: Integration and Testing

* [x] Update tools.py to expose new functions
* [x] Test API payload construction
* [x] Verify response handling
* [x] Document usage examples

## API Details

### API 1: Platform-based Product Integration

* **Endpoint** : `/ic-api/integration-monitoring/v1/integrations/metrics`
* **GroupBy** : platform
* **Metrics** : product
* **Usage** : Platform dropdown population, tab creation

### API 2: Product Count by Integration Type  

* **Endpoint** : `/ic-api/integration-monitoring/v1/integrations/metrics`
* **GroupBy** : product_integrated
* **Metrics** : product_count
* **Usage** : Product selection logic, integration health calculation

## Success Criteria

* [x] Both APIs successfully implemented and callable
* [x] Schema validation working correctly
* [x] Proper error handling and response formatting
* [x] Documentation updated with usage examples
* [x] Tool descriptions enhanced with UI functionality details

## Task Status: COMPLETED ✅

All implementation phases have been successfully completed. The integration monitoring APIs are now available with comprehensive tool descriptions that explain their purpose, UI functionality, and usage patterns.
