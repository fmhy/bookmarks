This repository is programmed to automatically generate browser bookmarks for the link collection FMHY.

Bookmarks are generated as HTML files which can be imported into any web browser.
![](https://i.imgur.com/N2Wfngc.png)

The HTML files are automatically updated weekly with the new changes from FMHY.

## Why?
Web browsers have auto-complete and search functions that are based on bookmarked pages, so its helpful to have interesting sites bookmarked, so you can find them quicker and make sure you are on the right URL.


## How does it look once imported?
![](https://i.imgur.com/h1GfL1W.png)


## How to download the importable HTML files?
![](https://i.imgur.com/e4xN3wy.png)


## How to import them into the browser?
![](https://i.imgur.com/6BpWb1q.png)

## How to add FMHY bookmarklet to Safari iOS?

1. Open Safari on your iOS device.
2. Tap the Share button (the square with an arrow pointing up).
3. Tap "Add Bookmark".
4. Name the bookmark "FMHY Bookmarklet" and save it to your desired location.
5. Tap the Share button again and tap "Add to Home Screen".
6. Name the shortcut "FMHY Bookmarklet" and tap "Add".
7. Open the "FMHY Bookmarklet" bookmark you just created.
8. Tap the address bar and delete the URL.
9. Copy and paste the following JavaScript code into the address bar:

```javascript
javascript:(function(){var script=document.createElement('script');script.src='https://raw.githubusercontent.com/fmhy/bookmarks/main/fmhy_bookmarklet.js';document.body.appendChild(script);})();
```

10. Tap "Go" on the keyboard to save the bookmarklet.
11. You can now use the FMHY bookmarklet by tapping the bookmark in Safari.

