"""End-to-end tests for frontend interactions"""

import pytest
from playwright.sync_api import Page, expect
import time
import os


@pytest.fixture(scope="session")
def frontend_url():
    """Get frontend URL from environment or use default"""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def api_url():
    """Get API URL from environment or use default"""
    return os.getenv("API_URL", "http://localhost:8000")


class TestFrontendE2E:
    """End-to-end tests for the frontend application"""
    
    def test_page_loads_successfully(self, page: Page, frontend_url: str):
        """Test that the main page loads without errors"""
        page.goto(frontend_url)
        
        # Check page title
        expect(page).to_have_title("天気コメント生成システム")
        
        # Check main elements are visible
        expect(page.locator("h1")).to_contain_text("天気コメント生成")
        expect(page.get_by_text("地点選択")).to_be_visible()
    
    def test_location_selection(self, page: Page, frontend_url: str):
        """Test location selection functionality"""
        page.goto(frontend_url)
        
        # Click on location selector
        location_selector = page.locator("[data-testid='location-selector']")
        location_selector.click()
        
        # Select a location
        page.get_by_text("東京").click()
        
        # Verify selection
        expect(location_selector).to_contain_text("東京")
    
    def test_comment_generation_flow(self, page: Page, frontend_url: str):
        """Test the complete comment generation flow"""
        page.goto(frontend_url)
        
        # Select location
        location_selector = page.locator("[data-testid='location-selector']")
        location_selector.click()
        page.get_by_text("東京").click()
        
        # Select LLM provider
        provider_selector = page.locator("[data-testid='llm-provider-selector']")
        provider_selector.click()
        page.get_by_text("Gemini").click()
        
        # Click generate button
        generate_button = page.get_by_role("button", name="コメント生成")
        generate_button.click()
        
        # Wait for loading to complete (max 30 seconds)
        page.wait_for_selector("[data-testid='loading-spinner']", state="hidden", timeout=30000)
        
        # Check results are displayed
        expect(page.locator("[data-testid='weather-comment']")).to_be_visible()
        expect(page.locator("[data-testid='advice-comment']")).to_be_visible()
        expect(page.locator("[data-testid='weather-data']")).to_be_visible()
    
    def test_error_handling(self, page: Page, frontend_url: str):
        """Test error handling in the UI"""
        page.goto(frontend_url)
        
        # Try to generate without selecting location
        generate_button = page.get_by_role("button", name="コメント生成")
        generate_button.click()
        
        # Should show error message
        expect(page.locator("[data-testid='error-message']")).to_be_visible()
        expect(page.locator("[data-testid='error-message']")).to_contain_text("地点を選択してください")
    
    def test_history_display(self, page: Page, frontend_url: str):
        """Test generation history display"""
        page.goto(frontend_url)
        
        # Generate a comment first
        location_selector = page.locator("[data-testid='location-selector']")
        location_selector.click()
        page.get_by_text("東京").click()
        
        generate_button = page.get_by_role("button", name="コメント生成")
        generate_button.click()
        
        # Wait for generation to complete
        page.wait_for_selector("[data-testid='loading-spinner']", state="hidden", timeout=30000)
        
        # Check history tab
        history_tab = page.get_by_role("tab", name="履歴")
        history_tab.click()
        
        # Should show the recent generation
        expect(page.locator("[data-testid='history-item']")).to_have_count(1)
        expect(page.locator("[data-testid='history-item']").first).to_contain_text("東京")
    
    def test_responsive_design(self, page: Page, frontend_url: str):
        """Test responsive design on different screen sizes"""
        page.goto(frontend_url)
        
        # Test mobile view
        page.set_viewport_size({"width": 375, "height": 667})
        expect(page.locator("[data-testid='mobile-menu']")).to_be_visible()
        
        # Test tablet view
        page.set_viewport_size({"width": 768, "height": 1024})
        expect(page.locator("[data-testid='sidebar']")).to_be_visible()
        
        # Test desktop view
        page.set_viewport_size({"width": 1920, "height": 1080})
        expect(page.locator("[data-testid='sidebar']")).to_be_visible()
    
    def test_api_integration(self, page: Page, frontend_url: str, api_url: str):
        """Test API integration"""
        # Check API health first
        api_response = page.request.get(f"{api_url}/health")
        assert api_response.ok
        assert api_response.json()["status"] == "ok"
        
        page.goto(frontend_url)
        
        # Monitor API calls
        with page.expect_request(lambda req: "/api/locations" in req.url) as locations_request:
            page.reload()
        
        # Verify locations were loaded
        assert locations_request.value.response().ok
    
    def test_weather_timeline_display(self, page: Page, frontend_url: str):
        """Test weather timeline visualization"""
        page.goto(frontend_url)
        
        # Generate comment with weather data
        location_selector = page.locator("[data-testid='location-selector']")
        location_selector.click()
        page.get_by_text("東京").click()
        
        generate_button = page.get_by_role("button", name="コメント生成")
        generate_button.click()
        
        # Wait for generation
        page.wait_for_selector("[data-testid='loading-spinner']", state="hidden", timeout=30000)
        
        # Check timeline is displayed
        timeline = page.locator("[data-testid='weather-timeline']")
        expect(timeline).to_be_visible()
        
        # Should have multiple time points
        time_points = timeline.locator("[data-testid='timeline-point']")
        expect(time_points).to_have_count_greater_than(0)
    
    def test_keyboard_navigation(self, page: Page, frontend_url: str):
        """Test keyboard navigation accessibility"""
        page.goto(frontend_url)
        
        # Tab through interactive elements
        page.keyboard.press("Tab")  # Focus on first element
        page.keyboard.press("Tab")  # Move to location selector
        
        # Open dropdown with Enter
        page.keyboard.press("Enter")
        
        # Navigate with arrow keys
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        
        # Tab to generate button
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        
        # Activate with Space
        page.keyboard.press("Space")
        
        # Check that generation started
        expect(page.locator("[data-testid='loading-spinner']")).to_be_visible()


class TestPerformanceE2E:
    """Performance-related E2E tests"""
    
    def test_page_load_performance(self, page: Page, frontend_url: str):
        """Test page load performance"""
        start_time = time.time()
        
        page.goto(frontend_url)
        page.wait_for_load_state("networkidle")
        
        load_time = time.time() - start_time
        
        # Page should load within 3 seconds
        assert load_time < 3.0
    
    def test_generation_performance(self, page: Page, frontend_url: str):
        """Test comment generation performance"""
        page.goto(frontend_url)
        
        # Setup
        location_selector = page.locator("[data-testid='location-selector']")
        location_selector.click()
        page.get_by_text("東京").click()
        
        # Measure generation time
        start_time = time.time()
        
        generate_button = page.get_by_role("button", name="コメント生成")
        generate_button.click()
        
        # Wait for completion
        page.wait_for_selector("[data-testid='loading-spinner']", state="hidden", timeout=30000)
        
        generation_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert generation_time < 15.0  # 15 seconds max