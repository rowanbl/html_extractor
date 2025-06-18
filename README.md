# html element extractor

*"I came, I saw, I stole your divs"* - Julius Caesar

## what is this thing?

ever looked at an element on a website and thought "i need that exact thing, but copying the html gives me a sad, naked div"? me too so i did this since all programmers do is take a 5 minute job and spend 4 hours automating it aparrently. onto websites it goes and steals html elements along with all their styling - even the responsive ones hiding in media queries. it tries to strip and ignore things that aren't used, but i've found https://uncss-online.com/ quite useful to finish the job, although I'm sure this won't be needed down the line if i ever improve this utility.

## features

- **precision theft** - Extracts exactly the element you want via XPath
- **persistent** - grabs all relevant css
- **responsive** - your stolen goods work on mobile too (because it gets the media queries)
- **drop-in ready** - clean html + css that Just Works™
- **headless mode** - stealthy (no browser window)

## installation

```bash
pip install selenium webdriver-manager
```

## usage

please don't repackage this into a tool / chrome extension or website and then charge money for it. keep it free and always link back to this repo if this code is used.

### command Line (quick & dirty)
```bash
python html_extractor.py https://example.com "//footer" stolen_footer.html
```

### python module (not really sure why you'd want this)
```python
from html_extractor import HTMLExtractor

extractor = HTMLExtractor(headless=True)
stolen_goods = extractor.extract_element(
    url="https://coolsite.com",
    xpath="//div[@class='amazing-component']",
    output_file="my_new_component.html"
)
```

## how it Works

1. opens a headless chrome browser
2. loads the target website
3. finds your element using xpath
4. analyzes all css rules and media queries
5. keeps only the styles that actually matter
6. packages everything into a neat little html file
7. disappears without a trace

## xpath examples

just to help you get how it works i guess. best way to get xcode is to right click on an element in inspect element then go into the copy submenu and then click copy full xcode path.

```bash
# Get the main navigation
"//nav[@class='main-nav']"

# Steal the dogs
"//footer[contains(@class, 'site-footer')]"

# That one div
"//div[@id='the-one-i-want']"
```

## requirements

- python 3+
- chrome browser (for the automation)
- questionable ethics

don't forget the python/pip modules listed above

## disclaimer

this tool is for educational purposes and legitimate web development (in my case I made it to get a footer from one subsidiary and reuse on another subsidiary... you'd think the repos would be shared between 2 companies owned by the same people but no). probably don't actually steal people's designs without permission

it's probably slow, inefficient, horrible to read, and generally not well written, but it does work and you end up with pretty much exactly what you want (far better than any chrome extension i tried and they usually also are locked behind paywalls) so just be patient and you'll get what you need

## contributing

found a bug? want to add features? go for it. tempted to rewrite in c at some point since this is a bit quick and dirty, so maybe someone wants to help with that

---

*Made with no ❤️ by Rowan*
