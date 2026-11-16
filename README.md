![go.hugobatista.com/intellireading](https://go.hugobatista.com/ghraw/intellireading-www/main/public/img/intellireading.png)
# Calibre Plugins

[![GitHub - Lint](https://go.hugobatista.com/gh/intellireading-calibre-plugins/actions/workflows/lint.yml/badge.svg)](https://go.hugobatista.com/gh/intellireading-calibre-plugins/actions/workflows/lint.yml)

**Th**is **re**po **cont**ains **th**e **sou**rce **co**de **fo**r [**Intelli**reading](https://go.hugobatista.com/intellireading) **Cali**bre **plug**ins. **The**se **plug**ins **all**ow **yo**u **t**o **gene**rate **metag**uided **vers**ions **o**f **yo**ur **eboo**ks, **b**y **implem**enting **a** **stream**lined **vers**ion **o**f **th**e [**Intelli**reading](https://go.hugobatista.com/intellireading) **algor**ithm, **usi**ng **th**e [**Cali**bre](https://calibre-ebook.com/) **ebo**ok **mana**ger.

Example of a text converted to a metaguided text:
![go.hugobatista.com/intellireading](https://go.hugobatista.com/ghraw/intellireading-www/main/public/img/sample.png) 


This repo is part of the [Intellireading](https://go.hugobatista.com/intellireading/) project, which aims to help people with dyslexia, ADHD, or anyone who wants to improve their reading focus and speed. 

## [Other Intellireading Code Repositories](https://go.hugobatista.com/ghstars/lists/intellireading)
- [Intellireading website](https://go.hugobatista.com/gh/intellireading-www), which allows anyone to convert an Epub to the metaguided version.
- [API Server](https://go.hugobatista.com/gh/intellireading-api_server), that support the Intellireading website.
- [CLI Tool](https://go.hugobatista.com/gh/intellireading-cli). A standalone tool and library that can be used to metaguide epub files.
- [Calibre Plugins](https://go.hugobatista.com/gh/intellireading-calibre-plugins). A set of plugins that can be used to metaguide epub files using Calibre.

## What is Epub Metaguiding?
**Metagu**iding **i**s **a** **techn**ique **th**at **ca**n **b**e **us**ed **t**o **impr**ove **yo**ur **read**ing **foc**us **an**d **spe**ed **(some**times **cal**led **Bio**nic **Readi**ng). **I**t **i**s **bas**ed **o**n **th**e **id**ea **th**at **yo**u **ca**n **us**e **a** **vis**ual **gui**de **t**o **he**lp **yo**ur **ey**es **foc**us **o**n **th**e **te**xt **yo**u **ar**e **read**ing. **I**n **th**is **cas**e, **th**e **vis**ual **gui**de **i**s **do**ne **b**y **bold**ing **a** **pa**rt **o**f **th**e **tex**t, **crea**ting **vis**ual **anch**ors **th**at **yo**ur **ey**es **ca**n **us**e **t**o **foc**us **o**n **th**e **tex**t. **Th**is **i**s **simi**lar **t**o **th**e **wa**y **a** **fin**ger **ca**n **b**e **us**ed **t**o **gui**de **yo**ur **ey**es **alo**ng **a** **li**ne **o**f **tex**t, **whi**ch **ha**s **be**en **sho**wn **t**o **impr**ove **read**ing **spe**ed **an**d **foc**us. ([**stu**dy: **"Do**es **finger-t**racking **poi**nt **t**o **chi**ld **read**ing **strate**gies"](https://ceur-ws.org/Vol-2769/paper_60.pdf))

**Howe**ver, **unl**ike **a** **fing**er, **th**e **vis**ual **gui**de **i**s **no**t **distra**cting, **an**d **i**t **ca**n **b**e **us**ed **t**o **gui**de **yo**ur **ey**es **alo**ng **mult**iple **lin**es **o**f **te**xt **a**t **onc**e. **Th**is **all**ows **yo**u **t**o **re**ad **fast**er, **an**d **wi**th **le**ss **effo**rt.

**Metagu**iding **i**s **partic**ulary **use**ful **fo**r **peo**ple **wi**th **dysl**exia **o**r **ADH**D, **bu**t **i**t **ca**n **b**e **us**ed **b**y **any**one **wh**o **wan**ts **t**o **impr**ove **the**ir **read**ing **foc**us **an**d **spe**ed. **Fo**r **mo**re **inform**ation, **vis**it **th**e [**Intelli**reading **webs**ite.](https://go.hugobatista.com/intellireading)

## Disable metaguiding

The **KoboTouch Metaguider** driver has an **Enable metaguiding** option, enabled by default. When it is disabled, books are sent without IntelliReading metaguiding. The Kobo driver's own settings, including KEPUB conversion, still apply. The experimental page-count correction is controlled separately by **Experimental: correct Kobo page counts for new books**.

## IntelliReading about page

By default, metaguided EPUBs include an IntelliReading about/donation page at the end. The page is added only when a book is metaguided for the first time; books that are already metaguided are copied unchanged.

You can disable the page in the settings of each plugin:

- **Epub Metaguider GUI (Interface Action)**: Preferences → Advanced → Plugins → EBook Metaguider (intellireading) → Customize plugin.
- **Epub Metaguider post processor (FileType)**: Preferences → Advanced → Plugins → EPUB Metaguider - Post Processor (intellireading) → Customize plugin.
- **Epub Metaguider output format (Output Format)**: when converting to EPUB, open the "Epub Output (metaguided)" section and uncheck "Add IntelliReading about/donation page".
- **KoboTouch Metaguider (Device Interface)**: Configure device → Collections, covers && uploads → IntelliReading → uncheck "Add IntelliReading about/donation page".

To remove the page from a book that was already metaguided, use "Remove metaguiding" and then metaguide the book again. "Remove metaguiding" always removes the about page, regardless of this setting.

## Fixation level

The fixation level controls how much of each word is bolded. It ranges from 1 (least bold) to 5 (most bold) and defaults to 3, which is the historical IntelliReading behaviour. Higher levels never bold less of each word.

You can change it in the settings of each plugin:

- **Epub Metaguider GUI (Interface Action)**: Preferences → Advanced → Plugins → EBook Metaguider (intellireading) → Customize plugin → Fixation level.
- **Epub Metaguider post processor (FileType)**: Preferences → Advanced → Plugins → EPUB Metaguider - Post Processor (intellireading) → Customize plugin → Fixation level.
- **Epub Metaguider output format (Output Format)**: when converting to EPUB, open the "Epub Output (metaguided)" section and choose a Fixation level.
- **KoboTouch Metaguider (Device Interface)**: Configure device → Collections, covers && uploads → IntelliReading → Fixation level.

The fixation level applies only to new conversions. EPUB files that are already metaguided are copied unchanged; use "Remove metaguiding" and then metaguide the book again to apply a different level. Standalone XHTML files have no metaguided marker, so avoid running metaguiding twice on the same file.

## Bold style

The bold style controls how the bold part of each word is rendered. The default is **Real bold**, which keeps the historical behaviour.

- **Real bold (tag)** — uses `<b>` and the font's bold face. This is the default.
- **Visual bold — shadow (same layout)** — uses `<b class="ir-bold">` plus a CSS `text-shadow`. The text keeps the original font metrics, so line breaks and page counts stay close to the original.
- **Visual bold — stroke (same layout)** — uses `<b class="ir-bold">` plus a CSS `-webkit-text-stroke`. It also keeps the original font metrics.

The visual modes are intended for Kobo kepubs and other WebKit-based readers. They avoid the page count changes that real bold can cause on a Kobo, because the text keeps the same width and line breaks. On readers that do not support those CSS properties, the text may render without emphasis; use **Real bold** for maximum compatibility. In particular, Kobo EPUB files (the Adobe/RMSDK renderer) may ignore the visual modes.

You can change the bold style in the settings of each plugin:

- **Epub Metaguider GUI (Interface Action)**: Preferences → Advanced → Plugins → EBook Metaguider (intellireading) → Customize plugin → Bold style.
- **Epub Metaguider post processor (FileType)**: Preferences → Advanced → Plugins → EPUB Metaguider - Post Processor (intellireading) → Customize plugin → Bold style.
- **Epub Metaguider output format (Output Format)**: when converting to EPUB, open the "Epub Output (metaguided)" section and choose a Bold style.
- **KoboTouch Metaguider (Device Interface)**: Configure device → Collections, covers && uploads → IntelliReading → Bold style.

The bold style applies only to new conversions. EPUB files that are already metaguided are copied unchanged; use "Remove metaguiding" and then metaguide the book again to apply a different style.

### Bold intensity

When the bold style is **Visual bold — shadow** or **Visual bold — stroke**, the **Bold intensity** setting controls how strong the effect is. It ranges from `1` (subtle) to `5` (strongest) and defaults to `3`.

Higher values make the shadow or stroke thicker. The text metrics do not change, so the page count stays close to the original. The setting is ignored when the style is **Real bold**.

You can change the intensity in the same places as the bold style:

- **Epub Metaguider GUI (Interface Action)**: Preferences → Advanced → Plugins → EBook Metaguider (intellireading) → Customize plugin → Bold intensity.
- **Epub Metaguider post processor (FileType)**: Preferences → Advanced → Plugins → EPUB Metaguider - Post Processor (intellireading) → Customize plugin → Bold intensity.
- **Epub Metaguider output format (Output Format)**: when converting to EPUB, open the "Epub Output (metaguided)" section and choose a Bold intensity.
- **KoboTouch Metaguider (Device Interface)**: Configure device → Collections, covers && uploads → IntelliReading → Bold intensity.

## What is Calibre?
**Cali**bre **i**s **a** **fr**ee **an**d **open-s**ource **e-b**ook **mana**ger. **I**t **i**s **us**ed **fo**r **catalo**ging, **conver**ting, **read**ing **an**d **sync**ing **e-bo**oks **wi**th **e-b**ook **rea**der **devi**ces. **I**t **i**s **prima**rily **a** **fr**ee **soft**ware **sui**te **devel**oped **b**y **use**rs **o**f **e-bo**oks **fo**r **use**rs **o**f **e-bo**oks.
**Fo**r **mo**re **inform**ation, **vis**it **th**e [**Cal**ibre **webs**ite](https://calibre-ebook.com/).


## Kobo page count correction (experimental)

On a Kobo, the total page count of a kepub is estimated from the word count of each chapter, not only from the rendered layout. The metaguiding markup can inflate that word count: a word such as `prefix` becomes `<b>pre</b>fix`, and the Kobo's word counter may count the two fragments as separate words. The per-chapter page count stays correct, but the total for the whole book can become too high.

The **KoboTouch Metaguider** driver can pre-create the Kobo database structure for a new KEPUB during transfer, using clean word counts computed on the host with a Kobo-compatible algorithm: each Han character counts as one word, and the remaining scripts use word boundaries. Because the chapter rows, the table of contents and the `volume_shortcovers` spine exist before the Kobo imports the book, the Kobo uses these counts and the footer shows the correct total. No reconnect is needed.

Enable **Experimental: correct Kobo page counts for new books** in the IntelliReading tab of the driver settings. It is disabled by default.

> **Back up your Kobo before enabling this option.** The page-count fix writes directly to the Kobo database. Keep a backup so you can restore it if something goes wrong.

- Only new `.kepub`/`.kepub.epub` uploads on the main memory are affected.
- Plain EPUB uploads (when KEPUB conversion is disabled), books on a memory card, and books without a readable TOC are not modified; the driver logs why.
- Books already on the device are not modified. To rebuild the page counts of an existing book, delete it from the Kobo and send it again with the option enabled.
- When metaguiding is disabled, no page-count rows are created.
- This feature is experimental and may change.

If the option is disabled, books are sent normally; the Kobo may show an inflated total for metaguided books that use partial-word bold.

## Calibre Plugins available

### Basic plugins
**The**se **plug**ins **ar**e **avail**able **i**n **th**e [**Cali**bre **Plu**gin **Sto**re](https://plugins.calibre-ebook.com/), **an**d **ca**n **b**e **insta**lled **fr**om **th**e **Cali**bre **inter**face. **Yo**u **ca**n **al**so **down**load **th**e **plug**ins **fr**om **th**is **rep**o, **an**d **inst**all **th**em **manua**lly. **Al**l **plug**ins **ar**e **compa**tible **wi**th **Cali**bre **6.5**.0 **an**d **abo**ve.

#### [Epub Metaguider GUI (Interface Action)](https://www.mobileread.com/forums/showthread.php?t=358615)
**Ad**ds **butt**ons **t**o **th**e **Cali**bre **inter**face, **allo**wing **yo**u **t**o **gene**rate **metag**uided **vers**ions **o**f **yo**ur **ebo**oks **fr**om **th**e **Ma**in **Tool**bar **o**r **th**e **Cont**ext **Men**u.
#### [KoboTouch Metaguider (Device Interface)](https://www.mobileread.com/forums/showthread.php?p=4533585)
**Exte**nds **th**e **KoboT**ouch **dri**ver, **allo**wing **yo**u **t**o **automa**tically **gene**rate **metag**uided **vers**ions **o**f **yo**ur **ebo**oks **wh**en **sen**ding **the**m **t**o **yo**ur **Ko**bo **devi**ce.

### Advanced plugins 
**Th**ese **plug**ins **ar**e **no**t **avail**able **i**n **th**e [**Cali**bre **Plu**gin **Sto**re](https://plugins.calibre-ebook.com/), **an**d **ca**n **b**e **insta**lled **fr**om **th**e **Cali**bre **inter**face **o**nly. **Down**load **the**se **plug**ins **fr**om **th**is **rep**o, **an**d **inst**all **th**em **manua**lly.
#### [Epub Metaguider output format (Output Format)](https://www.mobileread.com/forums/showthread.php?t=358616)
**Exte**nds **th**e **ep**ub **out**put **form**at, **allo**wing **yo**u **t**o **gene**rate **metag**uided **vers**ions **o**f **yo**ur **ebo**oks **wh**en **conve**rting **t**o **epu**b.
#### [Epub Metaguider post processor (FileType)](https://www.mobileread.com/forums/showthread.php?t=358613)
**Wor**ks **o**n **po**st **conve**rsion **an**d **po**st **impo**rt, **allo**wing **yo**u **t**o **gene**rate **metag**uided **vers**ions **o**f **yo**ur **ebo**oks **wh**en **conve**rting **t**o **ep**ub **o**r **impor**ting **ep**ub **fil**es.
