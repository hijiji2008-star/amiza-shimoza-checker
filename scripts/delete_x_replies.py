    import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        print("ブラウザを起動中...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://x.com/login")

        print("\nブラウザが開きました。Xにログインしてください。")
        print("ログインが完了したらここでEnterを押してください: ", end="", flush=True)
        input()

        # ユーザー名を自動検出
        try:
            await page.wait_for_selector('[data-testid="AppTabBar_Profile_Link"]', timeout=8000)
            profile_link = await page.query_selector('[data-testid="AppTabBar_Profile_Link"]')
            href = await profile_link.get_attribute('href')
            username = href.strip('/')
            print(f"ユーザー名を自動検出: @{username}")
        except:
            print("ユーザー名を入力してください（@なし）: ", end="", flush=True)
            username = input().strip().lstrip('@')

        print(f"\n@{username} の返信を全削除します。")
        print("Enterを押すと開始します: ", end="", flush=True)
        input()

        await page.goto(f"https://x.com/{username}/with_replies")
        await page.wait_for_timeout(3000)

        deleted_count = 0
        no_new_count = 0

        print("\n削除中... (しばらくお待ちください)\n")

        while True:
            tweets = await page.query_selector_all('article[data-testid="tweet"]')
            found_reply = False

            for tweet in tweets:
                try:
                    inner_text = await tweet.inner_text()
                    is_reply = (
                        "Replying to" in inner_text
                        or "返信先" in inner_text
                        or "に返信" in inner_text
                    )
                    if not is_reply:
                        continue

                    more_btn = await tweet.query_selector('[data-testid="caret"]')
                    if not more_btn:
                        continue

                    await more_btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(300)
                    await more_btn.click()
                    await page.wait_for_timeout(800)

                    delete_btn = None
                    for selector in [
                        'span:text-is("Delete")',
                        'span:text-is("削除")',
                    ]:
                        try:
                            delete_btn = await page.query_selector(selector)
                            if delete_btn:
                                break
                        except:
                            pass

                    if not delete_btn:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(300)
                        continue

                    await delete_btn.click()
                    await page.wait_for_timeout(800)

                    confirm_btn = await page.query_selector('[data-testid="confirmationSheetConfirm"]')
                    if confirm_btn:
                        await confirm_btn.click()
                        deleted_count += 1
                        print(f"削除完了: {deleted_count}件目", flush=True)
                        await page.wait_for_timeout(1500)
                        found_reply = True
                        break
                    else:
                        await page.keyboard.press("Escape")

                except Exception:
                    try:
                        await page.keyboard.press("Escape")
                    except:
                        pass
                    continue

            if not found_reply:
                old_height = await page.evaluate("document.documentElement.scrollHeight")
                await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                await page.wait_for_timeout(2500)
                new_height = await page.evaluate("document.documentElement.scrollHeight")

                if new_height == old_height:
                    no_new_count += 1
                    if no_new_count >= 3:
                        break
                else:
                    no_new_count = 0

        print(f"\n完了！合計 {deleted_count} 件の返信を削除しました。")
        print("\nEnterを押してブラウザを閉じます: ", end="", flush=True)
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
