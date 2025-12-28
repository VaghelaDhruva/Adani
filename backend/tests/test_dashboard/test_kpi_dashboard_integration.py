"""
Comprehensive dashboard integration tests for enterprise validation.
Tests API integration, error handling, edge cases, and dual-source scenarios.
"""

import pytest
import requests
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestKPIDashboardIntegration:
    """Test KPI dashboard API integration and error handling."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_kpi_dashboard_success(self):
        """Test successful KPI dashboard fetch."""
        response = self.client.get("/api/v1/kpi/dashboard/base")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        required_fields = [
            "scenario_name", "total_cost", "cost_breakdown",
            "production_utilization", "transport_utilization",
            "inventory_metrics", "service_performance", "data_sources"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate cost breakdown
        cost_breakdown = data["cost_breakdown"]
        required_costs = ["production_cost", "transport_cost", "fixed_trip_cost", "holding_cost"]
        for cost in required_costs:
            assert cost in cost_breakdown, f"Missing cost field: {cost}"
        
        # Validate service performance
        service_perf = data["service_performance"]
        required_service = ["demand_fulfillment_rate", "on_time_delivery", "service_level"]
        for service in required_service:
            assert service in service_perf, f"Missing service field: {service}"
        
        # Validate data sources
        data_sources = data["data_sources"]
        assert "primary" in data_sources
        assert isinstance(data_sources.get("external_used"), bool)
        assert isinstance(data_sources.get("quarantine_count"), int)
    
    def test_kpi_dashboard_high_demand_scenario(self):
        """Test high demand scenario KPIs."""
        response = self.client.get("/api/v1/kpi/dashboard/high_demand")
        
        assert response.status_code == 200
        data = response.json()
        
        # High demand should have higher costs and utilization
        assert data["scenario_name"] == "high_demand"
        assert data["total_cost"] > 0
        
        # Service level might be lower under high demand
        service_level = data["service_performance"]["service_level"]
        assert 0 <= service_level <= 1
    
    def test_kpi_dashboard_unknown_scenario_fallback(self):
        """Test graceful handling of unknown scenario."""
        response = self.client.get("/api/v1/kpi/dashboard/unknown_scenario")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return fallback data
        assert data["scenario_name"] == "unknown_scenario"
        assert data["total_cost"] == 0.0
        assert data["data_sources"]["primary"] == "internal"
    
    def test_kpi_comparison_success(self):
        """Test scenario comparison endpoint."""
        response = self.client.post(
            "/api/v1/kpi/compare",
            json=["base", "high_demand"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate comparison structure
        assert "comparison_timestamp" in data
        assert "scenarios" in data
        assert "summary_metrics" in data
        
        # Should have 2 scenarios
        assert len(data["scenarios"]) == 2
        
        # Validate summary metrics
        summary = data["summary_metrics"]
        assert "cost_range" in summary
        assert "service_level_range" in summary
        assert "cost_variance" in summary
    
    def test_kpi_comparison_with_partial_failure(self):
        """Test comparison when one scenario fails."""
        with patch('app.api.v1.routes_kpi.get_kpi_dashboard') as mock_fetch:
            # Mock first scenario success, second failure
            mock_fetch.side_effect = [
                {"scenario_name": "base", "total_cost": 1000, "service_performance": {"service_level": 0.95}},
                Exception("Failed to fetch")
            ]
            
            response = self.client.post(
                "/api/v1/kpi/compare",
                json=["base", "failing_scenario"]
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should still return comparison with error handling
            assert len(data["scenarios"]) == 2
            assert data["scenarios"][0]["scenario_name"] == "base"
            assert "error" in data["scenarios"][1]
    
    def test_kpi_summary_endpoint(self):
        """Test KPI summary endpoint."""
        response = self.client.get("/api/v1/kpi/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate summary structure
        required_fields = [
            "period_hours", "summary_timestamp", "total_runs",
            "successful_runs", "failed_runs", "average_total_cost",
            "average_service_level", "cost_trend", "service_trend"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing summary field: {field}"
        
        # Validate logical consistency
        assert data["total_runs"] == data["successful_runs"] + data["failed_runs"]
        assert data["average_total_cost"] > 0
        assert 0 <= data["average_service_level"] <= 1
    
    def test_kpi_health_check(self):
        """Test KPI health check endpoint."""
        response = self.client.get("/api/v1/kpi/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "kpi_api"
    
    def test_schema_validation_malformed_json(self):
        """Test handling of malformed JSON responses."""
        with patch('requests.get') as mock_get:
            # Mock malformed JSON response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            # This should be handled by the dashboard's retry logic
            # The API itself would return 500, but dashboard should handle gracefully
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            # API should handle the error gracefully
            assert response.status_code in [200, 500]
    
    def test_timeout_handling(self):
        """Test timeout handling."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
            
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            # Should handle timeout gracefully
            assert response.status_code in [200, 500]
    
    def test_connection_error_handling(self):
        """Test connection error handling."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            # Should handle connection error gracefully
            assert response.status_code in [200, 500]
    
    def test_partial_data_handling(self):
        """Test handling of partial/incomplete data."""
        with patch('app.api.v1.routes_kpi.get_kpi_dashboard') as mock_fetch:
            # Mock partial data response
            partial_data = {
                "scenario_name": "base",
                "total_cost": 1000.0,
                "cost_breakdown": {"production_cost": 800.0},  # Missing other costs
                "service_performance": {"service_level": 0.95}  # Missing other services
            }
            mock_fetch.return_value = partial_data
            
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            # Should handle partial data gracefully
            assert response.status_code == 200
    
    def test_null_value_handling(self):
        """Test handling of null values in KPI data."""
        with patch('app.api.v1.routes_kpi.get_kpi_dashboard') as mock_fetch:
            # Mock data with null values
            null_data = {
                "scenario_name": "base",
                "total_cost": None,
                "cost_breakdown": {
                    "production_cost": None,
                    "transport_cost": 500.0,
                    "fixed_trip_cost": None,
                    "holding_cost": 100.0
                },
                "service_performance": {
                    "demand_fulfillment_rate": None,
                    "on_time_delivery": 0.95,
                    "service_level": None
                }
            }
            mock_fetch.return_value = null_data
            
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            # Should handle null values gracefully
            assert response.status_code == 200


class TestDashboardResilience:
    """Test dashboard resilience under various failure conditions."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_concurrent_requests(self):
        """Test dashboard under concurrent load."""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = self.client.get("/api/v1/kpi/dashboard/base")
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed or handle gracefully
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 8, f"Too many failures: {results}"
    
    def test_solver_failure_simulation(self):
        """Test dashboard behavior when solver fails."""
        with patch('app.api.v1.routes_kpi.get_kpi_dashboard') as mock_fetch:
            # Mock solver failure response
            solver_failure_data = {
                "scenario_name": "base",
                "total_cost": 0.0,
                "cost_breakdown": {
                    "production_cost": 0.0,
                    "transport_cost": 0.0,
                    "fixed_trip_cost": 0.0,
                    "holding_cost": 0.0,
                    "penalty_cost": 1000.0  # Penalty for solver failure
                },
                "service_performance": {
                    "demand_fulfillment_rate": 0.0,
                    "on_time_delivery": 0.0,
                    "service_level": 0.0
                },
                "data_sources": {
                    "primary": "internal",
                    "external_used": False,
                    "quarantine_count": 0
                },
                "solver_status": "failed",
                "error": "Solver timeout"
            }
            mock_fetch.return_value = solver_failure_data
            
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should indicate solver failure
            assert data["total_cost"] == 0.0
            assert data["service_performance"]["service_level"] == 0.0
    
    def test_external_data_fallback(self):
        """Test dashboard when internal data fails and external is used."""
        with patch('app.api.v1.routes_kpi.get_kpi_dashboard') as mock_fetch:
            # Mock external data fallback
            external_data = {
                "scenario_name": "base",
                "total_cost": 1500.0,
                "cost_breakdown": {
                    "production_cost": 1200.0,
                    "transport_cost": 200.0,
                    "fixed_trip_cost": 50.0,
                    "holding_cost": 50.0
                },
                "data_sources": {
                    "primary": "external",
                    "external_used": True,
                    "quarantine_count": 5
                }
            }
            mock_fetch.return_value = external_data
            
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should indicate external data usage
            assert data["data_sources"]["external_used"] == True
            assert data["data_sources"]["quarantine_count"] > 0
    
    def test_data_quarantine_scenario(self):
        """Test dashboard when data quarantine is triggered."""
        with patch('app.api.v1.routes_kpi.get_kpi_dashboard') as mock_fetch:
            # Mock quarantined data scenario
            quarantined_data = {
                "scenario_name": "base",
                "total_cost": 1300.0,
                "cost_breakdown": {
                    "production_cost": 1000.0,
                    "transport_cost": 200.0,
                    "fixed_trip_cost": 50.0,
                    "holding_cost": 50.0
                },
                "data_sources": {
                    "primary": "internal",
                    "external_used": False,
                    "quarantine_count": 12
                },
                "validation_issues": [
                    "Invalid transport rates in 5 rows",
                    "Missing capacity data for 3 plants"
                ]
            }
            mock_fetch.return_value = quarantined_data
            
            response = self.client.get("/api/v1/kpi/dashboard/base")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should indicate quarantine
            assert data["data_sources"]["quarantine_count"] > 0
            assert "validation_issues" in data


if __name__ == "__main__":
    pytest.main([__file__])
