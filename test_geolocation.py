#!/usr/bin/env python3
"""
Test script to verify geolocation feature using Playwright
"""
import asyncio
from playwright.async_api import async_playwright

async def test_geolocation():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)

        # Create context with geolocation permission granted
        # Using New York City coordinates for testing
        context = await browser.new_context(
            geolocation={'latitude': 51.7128, 'longitude': 22.0060},
            permissions=['geolocation']
        )

        page = await context.new_page()

        # Track console messages
        async def handle_console(msg):
            print(f"CONSOLE [{msg.type}]: {msg.text}")

        async def handle_response(response):
            if '/api/nearby' in response.url:
                print(f"\n✓ API Response: {response.status} {response.url}")
                try:
                    data = await response.json()
                    print(f"✓ Found {len(data)} stations")
                    if len(data) > 0:
                        print(f"  First station: {data[0]['name']} - {data[0]['distance_km']:.2f} km away")
                except:
                    pass

        page.on("console", handle_console)
        page.on("response", handle_response)

        # Navigate to the UI
        print("\n=== Testing Geolocation Feature ===\n")
        print("1. Loading page...")
        await page.goto('http://localhost:8080/', wait_until='networkidle')
        print("✓ Page loaded\n")

        # Wait for map to initialize
        await page.wait_for_timeout(2000)

        # Click the "Find My Location" button
        print("2. Clicking 'Find My Location' button...")
        geolocate_btn = await page.query_selector('#geolocate-btn')

        if geolocate_btn:
            # Check button text before click
            btn_text = await page.locator('#geolocate-btn .text').inner_text()
            print(f"   Button text: '{btn_text}'")

            # Click the button
            await geolocate_btn.click()
            print("✓ Button clicked\n")

            # Wait a moment to see loading state
            await page.wait_for_timeout(500)

            # Check if button shows loading state
            loading_text = await page.locator('#geolocate-btn .text').inner_text()
            print(f"3. Loading state: '{loading_text}'")

            # Wait for geolocation and API call to complete
            print("\n4. Waiting for geolocation and API response...")
            await page.wait_for_timeout(5000)

            # Check for error or results
            error_msg = await page.query_selector('.error-message')
            if error_msg:
                error_text = await error_msg.inner_text()
                print(f"\n✗ Error: {error_text}")
            else:
                print("\n✓ No error message")

            # Check if results are displayed
            results_content = await page.query_selector('#results-content')
            if results_content:
                content_text = await results_content.inner_text()
                if 'Found' in content_text:
                    print(f"✓ Results displayed: {content_text[:100]}")
                elif 'No stations found' in content_text:
                    print(f"✓ Empty state displayed: {content_text[:100]}")
                else:
                    print(f"Results content: {content_text[:200]}")

            # Check button text is restored
            final_btn_text = await page.locator('#geolocate-btn .text').inner_text()
            print(f"\n5. Button text restored: '{final_btn_text}'")

            # Check if button is enabled again
            is_disabled = await geolocate_btn.is_disabled()
            print(f"   Button enabled: {not is_disabled}")

        else:
            print("✗ Geolocation button not found!")

        print("\n=== Test Complete ===")
        print("Browser will close in 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_geolocation())
