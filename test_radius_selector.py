#!/usr/bin/env python3
"""
Test script to verify radius selector functionality using Playwright
"""
import asyncio
from playwright.async_api import async_playwright

async def test_radius_selector():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)

        # Create context with geolocation permission granted
        # Using coordinates near populated area for better test results
        context = await browser.new_context(
            geolocation={'latitude': 51.7128, 'longitude': 22.0060},
            permissions=['geolocation']
        )

        page = await context.new_page()

        # Track API calls
        api_calls = []

        async def handle_response(response):
            if '/api/nearby' in response.url:
                print(f"✓ API call: {response.url}")
                try:
                    data = await response.json()
                    api_calls.append({
                        'url': response.url,
                        'count': len(data),
                        'data': data
                    })
                    print(f"  Found {len(data)} stations")
                except:
                    pass

        async def handle_console(msg):
            if 'radius' in msg.text.lower() or 'searching' in msg.text.lower():
                print(f"CONSOLE: {msg.text}")

        page.on("response", handle_response)
        page.on("console", handle_console)

        # Navigate to the UI
        print("\n=== Testing Radius Selector ===\n")
        print("1. Loading page...")
        await page.goto('http://localhost:8080/', wait_until='networkidle')
        print("✓ Page loaded\n")

        await page.wait_for_timeout(1500)

        # First, perform an initial search by clicking the map
        print("2. Performing initial search (click map)...")
        map_element = await page.query_selector('#map')
        bbox = await map_element.bounding_box()
        click_x = bbox['x'] + bbox['width'] / 2
        click_y = bbox['y'] + bbox['height'] / 2
        await page.mouse.click(click_x, click_y)
        await page.wait_for_timeout(3000)
        print(f"✓ Initial search complete: {api_calls[-1]['count']} stations found\n")

        # Get the radius selector
        radius_select = await page.query_selector('#radius-select')
        if not radius_select:
            print("✗ Radius selector not found!")
            await browser.close()
            return

        # Check current value
        current_value = await radius_select.get_attribute('value')
        print(f"3. Current radius: {current_value} km")

        # Test changing radius to 25km
        print("\n4. Changing radius to 25km...")
        initial_api_count = len(api_calls)
        await radius_select.select_option('25')

        # Wait for re-search to complete
        print("   Waiting for automatic re-search...")
        await page.wait_for_timeout(3000)

        # Check if new API call was made
        if len(api_calls) > initial_api_count:
            print(f"✓ Auto re-search triggered!")
            print(f"  New search found {api_calls[-1]['count']} stations within 25km")

            # Verify the URL contains the new radius
            last_url = api_calls[-1]['url']
            if 'km=25' in last_url:
                print("✓ API called with correct radius (25km)")
            else:
                print(f"✗ API called with wrong radius: {last_url}")
        else:
            print("✗ Auto re-search did NOT trigger")

        # Test changing radius to 5km
        print("\n5. Changing radius to 5km...")
        initial_api_count = len(api_calls)
        await radius_select.select_option('5')

        # Wait for re-search to complete
        print("   Waiting for automatic re-search...")
        await page.wait_for_timeout(3000)

        # Check if new API call was made
        if len(api_calls) > initial_api_count:
            print(f"✓ Auto re-search triggered!")
            print(f"  New search found {api_calls[-1]['count']} stations within 5km")

            # Verify the URL contains the new radius
            last_url = api_calls[-1]['url']
            if 'km=5' in last_url:
                print("✓ API called with correct radius (5km)")
            else:
                print(f"✗ API called with wrong radius: {last_url}")
        else:
            print("✗ Auto re-search did NOT trigger")

        # Check results panel is updated
        results_content = await page.query_selector('#results-content')
        content_text = await results_content.inner_text()
        if '5 km' in content_text:
            print("✓ Results panel shows updated radius (5 km)")
        else:
            print(f"Results panel text: {content_text[:100]}")

        # Summary
        print("\n=== Test Summary ===")
        print(f"Total API calls made: {len(api_calls)}")
        for i, call in enumerate(api_calls, 1):
            radius = 'unknown'
            if 'km=' in call['url']:
                radius = call['url'].split('km=')[1].split('&')[0]
            print(f"  {i}. Radius: {radius}km, Results: {call['count']} stations")

        print("\n✓ All tests completed!")
        print("Browser will close in 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_radius_selector())
