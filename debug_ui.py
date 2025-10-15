#!/usr/bin/env python3
"""
Debug script to inspect the map UI using Playwright
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_ui():
    async with async_playwright() as p:
        # Launch browser in headed mode so we can see what's happening
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Track network requests and responses
        requests = []
        responses = []

        async def handle_request(request):
            requests.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            })
            print(f"→ REQUEST: {request.method} {request.url}")

        async def handle_response(response):
            responses.append({
                'url': response.url,
                'status': response.status,
                'statusText': response.status_text
            })
            print(f"← RESPONSE: {response.status} {response.url}")

            # If this is the API call, print the response details
            if '/api/nearby' in response.url:
                print(f"   API Response Status: {response.status}")
                print(f"   API Response Text: {response.status_text}")
                try:
                    body = await response.text()
                    print(f"   API Response Body: {body[:500]}")  # First 500 chars
                except:
                    print("   Could not read response body")

        async def handle_console(msg):
            print(f"CONSOLE [{msg.type}]: {msg.text}")

        async def handle_page_error(error):
            print(f"PAGE ERROR: {error}")

        # Set up event listeners
        page.on("request", handle_request)
        page.on("response", handle_response)
        page.on("console", handle_console)
        page.on("pageerror", handle_page_error)

        # Navigate to the UI
        print("\n=== Navigating to http://localhost:8080/ ===\n")
        try:
            await page.goto('http://localhost:8080/', wait_until='networkidle', timeout=10000)
            print("\n=== Page loaded successfully ===\n")
        except Exception as e:
            print(f"\n=== ERROR loading page: {e} ===\n")
            await browser.close()
            return

        # Wait for the map to be initialized
        await page.wait_for_timeout(2000)

        # Check if the map element exists
        map_element = await page.query_selector('#map')
        if map_element:
            print("✓ Map element found")
        else:
            print("✗ Map element NOT found")

        # Try to click on the map to trigger a search
        print("\n=== Clicking on the map to trigger a search ===\n")
        try:
            # Get the map element's bounding box
            bbox = await map_element.bounding_box()
            if bbox:
                # Click in the center of the map
                click_x = bbox['x'] + bbox['width'] / 2
                click_y = bbox['y'] + bbox['height'] / 2
                print(f"Clicking at ({click_x}, {click_y})")
                await page.mouse.click(click_x, click_y)

                # Wait for the API call to complete
                print("\nWaiting for API call to complete...")
                await page.wait_for_timeout(3000)
            else:
                print("Could not get map bounding box")
        except Exception as e:
            print(f"Error clicking map: {e}")

        # Check for any error messages in the UI
        print("\n=== Checking for error messages in UI ===\n")
        error_msg = await page.query_selector('.error-message')
        if error_msg:
            error_text = await error_msg.inner_text()
            print(f"✗ Error message found: {error_text}")
        else:
            print("✓ No error message found")

        # Print summary
        print("\n=== SUMMARY ===")
        print(f"Total requests made: {len(requests)}")
        print(f"Total responses received: {len(responses)}")

        api_calls = [r for r in requests if '/api/nearby' in r['url']]
        print(f"\nAPI calls to /api/nearby: {len(api_calls)}")
        if api_calls:
            for call in api_calls:
                print(f"  - {call['url']}")

        # Wait a bit before closing to see the state
        print("\nBrowser will close in 5 seconds...")
        await page.wait_for_timeout(5000)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_ui())
