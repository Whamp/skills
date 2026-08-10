# Wikipedia AI Artifacts

Use this only for Wikipedia-style articles, citations, markup, edit summaries, and AFC drafts. For ordinary prose, use `ai-writing-patterns.md`.

## Contents

- Markup tells: Markdown in wikitext, ChatGPT-specific markup, reference markup bugs, attribution fields, and stray categories
- Citation tells: hallucinated references, broken links, invalid DOI/ISBN values, unconventional references, UTM parameters, and unused named refs
- Style discrepancies: cut-offs, style shifts, English-variety shifts, verbose edit summaries, and AFC templates
- Human-writing and ineffective indicators

## Markup

### Use of Markdown

AI chatbots are not proficient in [wikitext](https://en.wikipedia.org/wiki/H:WT "H:WT"), the [markup language](https://en.wikipedia.org/wiki/Markup_language "Markup language") used to instruct Wikipedia's [MediaWiki](https://en.wikipedia.org/wiki/MediaWiki "MediaWiki") software how to format an article. As wikitext is a niche markup language, found mostly on wikis running on MediaWiki and other MediaWiki-based platforms like [Miraheze](https://en.wikipedia.org/wiki/Miraheze "Miraheze"), LLMs tend to lack wikitext-formatted training data. While the corpora of chatbots did ingest millions of Wikipedia articles, these articles would not have been processed as text files containing wikitext syntax. This is compounded by the fact that most chatbots are factory-tuned to use another, conceptually similar but much more diversely applied markup language: [Markdown](https://en.wikipedia.org/wiki/Markdown "Markdown"). Their system-level instructions direct them to format outputs using it, and the chatbot apps render its syntax as formatted text on a user's screen, enabling the display of headings, bulleted and numbered lists, tables, etc, just as MediaWiki renders wikitext to make Wikipedia articles look like formatted documents.

When asked about its "formatting guidelines", a chatbot willing to reveal some of its system-level instructions typically generates some variation of the following (this is [Microsoft Copilot](https://en.wikipedia.org/wiki/Microsoft_Copilot "Microsoft Copilot") in mid-2025):

> ## Formatting Guidelines
>
> - All output uses GitHub-flavored Markdown.
> - Use a single main title (`#`) and clear primary subheadings (`##`).
> - Keep paragraphs short (3–5 sentences, ≤150 words).
> - Break large topics into labeled subsections.
> - Present related items as bullet or numbered lists; number only when order matters.
> - Always leave a blank line before and after each paragraph.
> - Avoid bold or italic styling in body text unless explicitly requested.
> - Use horizontal dividers (`---`) between major sections.
> - Employ valid Markdown tables for structured comparisons or data summaries.
> - Refrain from complex Unicode symbols; stick to simple characters.
> - Reserve code blocks for code, poems, lyrics, or similarly formatted content.
> - For mathematical expressions, use LaTeX outside of code blocks.

As the above suggests, Markdown's syntax is completely different from wikitext's: Markdown uses asterisks (*) or underscores (_) instead of single-quotes (') for bold and italic formatting, hash symbols (#) instead of equals signs (=) for section headings, parentheses (()) instead of square brackets ([]) around URLs, and three symbols (---, ***, or ___) instead of four hyphens (----) for thematic breaks.

Even when they are told to do so explicitly, chatbots generally struggle to generate text using syntactically correct wikitext, as their training data lead to a drastically greater affinity for and fluency in Markdown. When told to "generate an article", a chatbot typically defaults to using Markdown for the generated output, which is preserved in clipboard text by the copy functions on some chatbot platforms. If instructed to generate content for Wikipedia, the chatbot might "realize" the need to generate Wikipedia-compatible code, and might include a message like "Would you like me to ... turn this into actual Wikipedia markup format (`wikitext`)?"[^b] in its output. If the chatbot is told to proceed, the resulting syntax is often rudimentary, syntactically incorrect, or both. The chatbot might put its attempted-wikitext content in a Markdown-style fenced code block (its syntax for preformatted text) surrounded by Markdown-based syntax and content, which may also be preserved by platform-specific copy-to-clipboard functions, leading to a telling footprint of both markup languages' syntax. This might include the appearance of three backticks in the text, such as: ` ```wikitext `.[^c]

The presence of faulty wikitext syntax mixed with Markdown syntax is a strong indicator that content is LLM-generated, especially if in the form of a fenced Markdown code block. However, Markdown *alone* is not such a strong indicator. Software developers, researchers, technical writers, and experienced internet users frequently use Markdown in tools like [Obsidian](https://en.wikipedia.org/wiki/Obsidian_(software) "Obsidian (software)") and [GitHub](https://en.wikipedia.org/wiki/GitHub_Flavored_Markdown "GitHub Flavored Markdown"), and on platforms like Reddit, Discord, and Slack. Some writing tools and apps, such as iOS Notes, Google Docs, and Windows Notepad, support Markdown editing or exporting. The increasing ubiquity of Markdown may also lead new editors to expect or assume Wikipedia to support Markdown by default.

**Examples**

> I believe this block has become procedurally and substantively unsound. Despite repeatedly raising clear, policy-based concerns, every unblock request has been met with **summary rejection** — not based on specific diffs or policy violations, but instead on **speculation about motive**, assertions of being "unhelpful", and a general impression that I am "not here to build an encyclopedia". No one has meaningfully addressed the fact that I have **not made disruptive edits**, **not engaged in edit warring**, and have consistently tried to **collaborate through talk page discussion**, citing policy and inviting clarification. Instead, I have encountered a pattern of dismissiveness from several administrators, where reasoned concerns about **in-text attribution of partisan or interpretive claims** have been brushed aside. Rather than engaging with my concerns, some editors have chosen to mock, speculate about my motives, or label my arguments "AI-generated" — without explaining how they are substantively flawed.

> - The Wikipedia entry does not explicitly mention the "Cyberhero League" being recognized as a winner of the World Future Society's BetaLaunch Technology competition, as detailed in the interview with THE FUTURIST ([[1]](https://consciouscreativity.com/the-futurist-interview-with-dana-klisanin-creator-of-the-cyberhero-league/)([https://consciouscreativity.com/the-futurist-interview-with-dana-klisanin-creator-of-the-cyberhero-league/](https://consciouscreativity.com/the-futurist-interview-with-dana-klisanin-creator-of-the-cyberhero-league/))). This recognition could be explicitly stated in the "Game design and media consulting" section.

Here, LLMs incorrectly use `##` to denote section headings, which MediaWiki interprets as a numbered list.

> 1. 1. Geography
>
> Villers-Chief is situated in the [Jura Mountains](https://en.wikipedia.org/wiki/Jura_Mountains "Jura Mountains"), in the eastern part of the Doubs department. [...]
>
> 1. 1. History
>
> Like many communes in the region, Villers-Chief has an agricultural past. [...]
>
> 1. 1. Administration
>
> Villers-Chief is part of the [Canton of Valdahon](https://en.wikipedia.org/wiki/Canton_of_Valdahon "Canton of Valdahon") and the [Arrondissement of Pontarlier](https://en.wikipedia.org/wiki/Arrondissement_of_Pontarlier "Arrondissement of Pontarlier"). [...]
>
> 1. 1. Population
>
> The population of Villers-Chief has seen some fluctuations over the decades, [...]

Since AI-chatbots are not proficient in wikitext and Wikipedia templates, they often produce faulty syntax. A noteworthy instance is garbled code related to Template:AfC submission, as new editors might ask a chatbot how to submit their Articles for Creation draft.

**Examples**

Note the badly malformed category link which appears to be a result of code that provides day information in the LLM's Markdown parser:

```
[[Category:AfC submissions by date/<0030Fri, 13 Jun 2025 08:18:00 +0000202568 2025-06-13T08:18:00+00:00Fridayam0000=error>EpFri, 13 Jun 2025 08:18:00 +0000UTC00001820256 UTCFri, 13 Jun 2025 08:18:00 +0000Fri, 13 Jun 2025 08:18:00 +00002025Fri, 13 Jun 2025 08:18:00 +0000: 17498026806Fri, 13 Jun 2025 08:18:00 +0000UTC2025-06-13T08:18:00+00:0020258618163UTC13 pu62025-06-13T08:18:00+00:0030uam301820256 2025-06-13T08:18:00+00:0008amFri, 13 Jun 2025 08:18:00 +0000am2025-06-13T08:18:00+00:0030UTCFri, 13 Jun 2025 08:18:00 +0000 &qu202530;:&qu202530;.</0030Fri, 13 Jun 2025 08:18:00 +0000202568>June 2025|sandbox]]
```

### ChatGPT-specific markup: citeturn, iturn

ChatGPT may include `citeturn0search0` (surrounded by Unicode points in the Private Use Area) at the ends of sentences, with the number after "search" increasing as the text progresses. These are places where the chatbot links to an external site, but a human pasting the conversation into Wikipedia has that link converted into placeholder code. This was first observed in February 2025.

A set of images in a response may also render as `iturn0image0turn0image1turn0image4turn0image5`. Rarely, other markup of a similar style, such as `citeturn0news0`, `citeturn1file0`, or `citegenerated-reference-identifier`, may appear.

**Examples**

> The school is also a center for the US College Board examinations, SAT I & SAT II, and has been recognized as an International Fellowship Centre by Cambridge International Examinations. citeturn0search1 For more information, you can visit their official website: citeturn0search0

### Reference markup bugs: contentReference, oaicite, oai_citation, attached_file, grok_card

Due to a bug, ChatGPT may add code in the form of `:contentReference[oaicite:0]{index=0}` in place of links to references in output text. Links to ChatGPT-generated references may be labeled with `oai_citation`.

**Examples**

> :contentReference[oaicite:16]{index=16}
>
> 1. **Ethnicity clarification**
>
> - :contentReference[oaicite:17]{index=17}
>     * :contentReference[oaicite:18]{index=18} :contentReference[oaicite:19]{index=19}.
>     * Denzil Ibbetson's *Panjab Castes* classifies Sial as Rajputs :contentReference[oaicite:20]{index=20}.
>     * Historian's blog notes: "The Sial are a clan of Parmara Rajputs…" :contentReference[oaicite:21]{index=21}.
> 2. :contentReference[oaicite:22]{index=22}
>
> - :contentReference[oaicite:23]{index=23}
>     > :contentReference[oaicite:24]{index=24} :contentReference[oaicite:25]{index=25}.

> #### Key facts needing addition or correction:
>
> 1. **Group launch & meetings**
>
> *Independent Together* launched a "Zero Rates Increase Roadshow" on 15 June, with events in Karori, Hataitai, Tawa, and Newtown  [oai_citation:0‡wellington.scoop.co.nz](https://wellington.scoop.co.nz/?p=171473&utm_source=chatgpt.com).
>
> 2. **Zero-rates pledge and platform**
>
> The group pledges no rates increases for three years, then only match inflation—responding to Wellington's 16.9% hike for 2024/25  [oai_citation:1‡en.wikipedia.org](https://en.wikipedia.org/wiki/Independent_Together?utm_source=chatgpt.com).

As of fall 2025, tags like `[attached_file:1]`, `[web:1]` have been seen at the end of sentences. This may be Perplexity-specific.[^12]

> During his time as CEO, Philip Morris's reputation management and media relations brought together business and news interests in ways that later became controversial, with effects still debated in contemporary regulatory and legal discussions.[attached_file:1]

Though Grok-generated text is rare compared to other chatbots, it may sometimes include XML-styled *grok_card* tags after citations.

> Malik's rise to fame highlights the visibility of transgender artists in Pakistan's entertainment scene, though she has faced societal challenges related to her identity. [...]<grok-card data-id="e8ff4f" data-type="citation_card">

### attribution and attributableIndex

ChatGPT may add JSON-formatted code at the end of sentences in the form of `({"attribution":{"attributableIndex":"X-Y"}})`, with X and Y being increasing numeric indices.

**Examples**

> ^[Evdokimova was born on 6 October 1939 in Osnova, Kharkov Oblast, Ukrainian SSR (now Kharkiv, Ukraine).&#93;({"attribution":{"attributableIndex":"1009-1"}}) ^[She graduated from the Gerasimov Institute of Cinematography (VGIK) in 1963, where she studied under Mikhail Romm.&#93;({"attribution":{"attributableIndex":"1009-2"}}) [oai_citation:0‡IMDb](https://www.imdb.com/name/nm0947835/?utm_source=chatgpt.com) [oai_citation:1‡maly.ru](https://www.maly.ru/en/people/EvdokimovaA?utm_source=chatgpt.com)

> Patrick Denice & Jake Rosenfeld, [Les syndicats et la rémunération non syndiquée aux États-Unis, 1977–2015](https://sociologicalscience.com/articles-v5-23-541/), ''Sociological Science'' (2018).&#93;({"attribution":{"attributableIndex":"3795-0"}})

### Non-existent or out-of-place categories and "see also" pages

LLMs may hallucinate non-existent categories, sometimes for generic concepts that *seem like* plausible category titles (or SEO keywords), and sometimes because their training set includes obsolete and renamed categories. These will appear as red links. You may also find category redirects, such as the longtime spammer favorite Category:Entrepreneurs. Sometimes, broken categories may be deleted by reviewers, so if you suspect a page may be LLM-generated, it may be worth checking earlier revisions.

Pay attention to blue links under "see also" headers as well. LLM-generated "see also" sections often tend to fill them up (to at least three links) seemingly out of obligation. If a new page/draft on some startup links to a broad term like Financial technology in its see-also section, that's a bit suspicious.

Of course, none of this section should be treated as a hard-and-fast rule. New users are unlikely to know about Wikipedia's style guidelines for these sections, and returning editors may be used to old categories that have since been deleted.

**Examples**

```
[[Category:American hip hop musicians]]
```

rather than

```
[[Category:American hip-hop musicians]]
```

---

## Citations

### Fictitious or hallucinated references

LLMs may generate fictitious or hallucinated references that do not exist or contain fabricated information.

### Broken external links

If a new article or draft has multiple citations with external links, and several of them are broken (e.g., returning [404 errors](https://en.wikipedia.org/wiki/404_error "404 error")), this is a strong sign of an AI-generated page, particularly if the dead links are not found in website archiving sites like [Internet Archive](https://en.wikipedia.org/wiki/Internet_Archive "Internet Archive") or [Archive Today](https://en.wikipedia.org/wiki/Archive_Today "Archive Today"). Most links [become broken over time](https://en.wikipedia.org/wiki/Link_rot "Link rot"), but these factors make it unlikely that the link was ever real.

### Invalid DOI and ISBNs

A [checksum](https://en.wikipedia.org/wiki/Checksum "Checksum") can be used to verify [ISBNs](https://en.wikipedia.org/wiki/ISBN "ISBN"). An invalid checksum is a very likely sign that an ISBN is incorrect, and citation templates display a warning if so. Similarly, [DOIs](https://en.wikipedia.org/wiki/Digital_object_identifier "Digital object identifier") are more resistant to link rot than regular hyperlinks. Unresolvable DOIs and invalid ISBNs can be indicators of [hallucinated](https://en.wikipedia.org/wiki/Hallucination_(AI) "Hallucination (AI)") references.

Related are DOIs that point to entirely unrelated articles and general book citations without pages. This passage, for example, was generated by ChatGPT.

> Ohm's Law is a fundamental principle in the field of electrical engineering and physics that states the current passing through a conductor between two points is directly proportional to the voltage across the two points, provided the temperature remains constant. Mathematically, it is expressed as V=IR, where V is the voltage, I is the current, and R is the resistance. The law was formulated by German physicist Georg Simon Ohm in 1827, and it serves as a cornerstone in the analysis and design of electrical circuits [1]. Ohm's Law applies to many materials and components that are "ohmic," meaning their resistance remains constant regardless of the applied voltage or current. However, it does not hold for non-linear devices like diodes or transistors [2][3].
>
> References:
>
> 1. Dorf, R. C., & Svoboda, J. A. (2010). Introduction to Electric Circuits (8th ed.). Hoboken, NJ: John Wiley & Sons. ISBN 9780470521571.
>
> 2. M. E. Van Valkenburg, "The validity and limitations of Ohm's law in non-linear circuits," Proceedings of the IEEE, vol. 62, no. 6, pp. 769–770, Jun. 1974. doi:10.1109/PROC.1974.9547
>
> 3. C. L. Fortescue, "Ohm's Law in alternating current circuits," Proceedings of the IEEE, vol. 55, no. 11, pp. 1934–1936, Nov. 1967. doi:10.1109/PROC.1967.6033

The book references appear valid – a book on electric circuits would likely have information about Ohm's law – but without the page number, that citation is not useful for verifying the claims in the prose. Worse, both *Proceedings of the IEEE* citations are completely made up. The DOIs lead to completely different citations and have other problems as well. For instance, [C. L. Fortescue](https://en.wikipedia.org/wiki/Charles_LeGeyt_Fortescue "Charles LeGeyt Fortescue") was dead for 30+ years at the purported time of writing, and Vol 55, Issue 11 does not list any articles that match anything remotely close to the information given in reference 3.

### Incorrect or unconventional use of references

AI tools may have been prompted to include references, and make an attempt to do so as Wikipedia expects, but fail with some key implementation details or stand out when compared with conventions.

**Examples**

In the below example, note the incorrect attempt at re-using references. The tool used here was not capable of searching for non-confabulated sources (as it was done the day before Bing Deep Search launched) but nonetheless found one real reference. The syntax for re-using the references was incorrect.

In this case, the *Smith, R. J.* source – being the "third source" the tool presumably generated the link 'https://pubmed.ncbi.nlm.nih.gov/3' (which has a PMID reference of 3) – is also completely irrelevant to the body of the article. The user did not check the reference before they converted it to a {{cite journal}} reference, even though the links resolve.

The LLM in this case has diligently included the incorrect re-use syntax after every single full stop.

> For over thirty years, computers have been utilized in the rehabilitation of individuals with brain injuries. Initially, researchers delved into the potential of developing a "prosthetic memory."<ref>Fowler R, Hart J, Sheehan M. A prosthetic memory: an application of the prosthetic environment concept. *Rehabil Counseling Bull*. 1972;15:80–85.</ref> However, by the early 1980s, the focus shifted towards addressing brain dysfunction through repetitive practice.<ref>{{Cite journal |last=Smith |first=R. J. |last2=Bryant |first2=R. G. |date=1975-10-27 |title=Metal substitutions incarbonic anhydrase: a halide ion probe study |url=https://pubmed.ncbi.nlm.nih.gov/3 |journal=Biochemical and Biophysical Research Communications |volume=66 |issue=4 |pages=1281–1286 |doi=10.1016/0006-291x(75)90498-2 |issn=0006-291X |pmid=3}}</ref> Only a few psychologists were developing rehabilitation software for individuals with Traumatic Brain Injury (TBI), resulting in a scarcity of available programs.<sup>[3]</sup> Cognitive rehabilitation specialists opted for commercially available computer games that were visually appealing, engaging, repetitive, and entertaining, theorizing their potential remedial effects on neuropsychological dysfunction.<sup>[3]</sup>

Some LLMs or chatbot interfaces use the character ↩ to indicate footnotes:

> References
>
> Would you like help formatting and submitting this to Wikipedia, or do you plan to post it yourself? I can guide you step-by-step through that too.
>
> **Footnotes**
>
> 1.   KLAS Research. (2024). *Top Performing RCM Vendors 2024*. https://klasresearch.com ↩ ↩2
> 2.   PR Newswire. (2025, February 18). *CureMD AI Scribe Launch Announcement*. https://www.prnewswire.com/news-releases/curemd-ai-scribe ↩

### ChatGPT-specific UTM parameters

ChatGPT may add the [UTM parameter](https://en.wikipedia.org/wiki/UTM_parameter "UTM parameter") `utm_source=openai` or, in edits prior to August 2025, `utm_source=chatgpt.com` to URLs that it is using as sources. Other LLMs, such as Gemini or Claude, use UTM parameters less often.[^13]

Note: While this does definitively prove ChatGPT's involvement, it doesn't prove, on its own, that ChatGPT also generated the writing. Some editors use AI tools to find citations for existing text; this will be apparent in the edit history.

**Examples**

> Following their marriage, Burgess and Graham settled in Cheshire, England, where Burgess serves as the head coach for the Warrington Wolves rugby league team. [https://www.theguardian.com/sport/2025/feb/11/sam-burgess-interview-warrington-rugby-league-luke-littler?utm_source=chatgpt.com]

> Vertex AI documentation and blog posts describe watermarking, verification workflow, and configurable safety filters (for example, person‑generation controls and safety thresholds). ([cloud.google.com](https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images?utm_source=openai))

### Named references declared in references section but unused in article body

*This section is empty.* You can help by adding to it. *(October 2025)*

**Examples**

See these diffs for examples. The problematic references appear as parser errors in the reflist.

- [Special:PermanentLink/1287201002#References](https://en.wikipedia.org/wiki/Special:PermanentLink/1287201002#References "Special:PermanentLink/1287201002")
- [Special:PermanentLink/1292432848#References](https://en.wikipedia.org/wiki/Special:PermanentLink/1292432848#References "Special:PermanentLink/1292432848")
- [Special:PermanentLink/1291491974#References](https://en.wikipedia.org/wiki/Special:PermanentLink/1291491974#References "Special:PermanentLink/1291491974")
- [Special:PermanentLink/1291561040#References](https://en.wikipedia.org/wiki/Special:PermanentLink/1291561040#References "Special:PermanentLink/1291561040")

---

## Discrepancies in Writing Style and Variety of English

### Abrupt cut offs

AI tools may abruptly stop generating content, for example if they predict the end of text sequence (appearing as `<|endoftext|>`) next. Also, the number of tokens that a single response has is usually limited, and further responses require the user to select "continue generating".

This method is not foolproof, as a malformed copy/paste from one's local computer can also cause this. It may also indicate a copyright violation rather than the use of an LLM.

### Sudden shift in writing style

A sudden shift in an editor's writing style, such as unexpectedly flawless grammar compared to their other communication, may indicate the use of AI tools.

### Sudden shift in English variety use

A mismatch of user location, national ties of the topic to a variety of English, and the variety of English used may indicate the use of AI tools. A human writer from India writing about an Indian university would probably not use American English; however, LLM outputs use American English by default, unless prompted otherwise.[^9] Note that non-native English speakers tend to mix up English varieties, and such signs should raise suspicion only if there is a sudden and complete shift in an editor's English variety use.

### Overwhelmingly verbose edit summaries

AI-generated [edit summaries](https://en.wikipedia.org/wiki/Help:Edit_summary "Help:Edit summary") are often unusually long, written as formal, first-person paragraphs without abbreviations, and/or conspicuously itemize Wikipedia's conventions.

> Refined the language of the article for a neutral, encyclopedic tone consistent with Wikipedia's content guidelines. Removed promotional wording, ensured factual accuracy, and maintained a clear, well-structured presentation. Updated sections on history, coverage, challenges, and recognition for clarity and relevance. Added proper formatting and categorized the entry accordingly

> I formalized the tone, clarified technical content, ensured neutrality, and indicated citation needs. Historical narratives were streamlined, allocation details specified with regulatory references, propagation explanations made reader-friendly, and equipment discussions focused on availability and regulatory compliance, all while adhering to encyclopedic standards.

> **Concise edit summary:** Improved clarity, flow, and readability of the plot section; reduced redundancy and refined tone for better encyclopedic style.

### "Submission statements" in AFC drafts

This one is specific to drafts submitted by Articles for Creation. At least one LLM tends to insert "submission statements" supposedly intended for reviewers that supposedly explain why the subject is notable and why the draft meets Wikipedia guidelines. Of course, all this actually does is let reviewers know that the draft is LLM-generated, and should be declined or speedied without a second thought.

> Reviewer note (for AfC): This draft is a neutral and well-sourced biography of Portuguese public manager Jorge Patrão. All references are from independent, reliable sources (Público, Diário de Notícias, Jornal de Negócios, RTP, O Interior, Agência Lusa) covering his public career and cultural activity. It meets WP:RS and WP:BLP standards and demonstrates clear notability per WP:NBIO through: – Presidency of Serra da Estrela Tourism Region (1998–2013); – Presidency of Parkurbis – Covilhã Science and Technology Park; – Founding role in Rede de Judiarias de Portugal (member of the Council of Europe's European Routes of Jewish Heritage); – Authorship of the book "1677 – A Fábrica d'El-Rei"; – Founder/curator of the Beatriz de Luna Art Collection (Old Master focus). There is also a Portuguese version of this article at pt.wikipedia.org/wiki/Jorge_Patrão. Thank you for your review. -->

— Found at the top of Draft:Jorge Patrão (all the inevitable formatting errors are present in the original)

### Pre-declined AFC review templates

Occasionally a new editor creates a draft that includes an AFC review template already set to "declined". The template is also devoid of content with no reviewer reasoning given. The LLM apparently offers to add an AFC submission template to the draft, and then provides something like `{{AfC submission|d}}`, in which the "d" parameter pre-declines the draft by substituting {{AfC submission/declined}}. The draft's contribution history reveals that this template was inserted at some point by the draft's creator. Invariably the creator then asks on Wikipedia:WikiProject Articles for creation/Help desk or one of the other help pages why the draft was declined with no feedback. The presence of a content-free "submission declined" header is a **strong** indicator that the draft was LLM-generated.

---

## Signs of Human Writing

### Age of text relative to ChatGPT launch

ChatGPT was launched to the public on November 30, 2022. Although OpenAI had similarly powerful LLMs before then, they were paid services and not easily accessible or known to lay people. ChatGPT experienced extreme growth immediately on launch.

It is very unlikely that any particular text added to Wikipedia **prior to November 30, 2022** was generated by an LLM. If an edit was made before this date, AI use can be safely ruled out for that revision. While some older text may display some of the AI signs given in this list, and even convincingly appear to have been AI-generated, the vastness of Wikipedia allows for these rare coincidences.

### Ability to explain one's own editorial choices

Editors should be able to explain why they made one or more edits or mistakes. For example, if an editor inserts a URL that appears fabricated, you can ask how the mix-up occurred instead of jumping to conclusions. If they can supply the correct link and explain it as a human error (perhaps a typo), or share the relevant passage from the real source, that points to an ordinary human error.

---

## Ineffective Indicators

False accusations of AI use can [drive away new editors](https://en.wikipedia.org/wiki/Wikipedia:BITE "Wikipedia:BITE") and foster an atmosphere of suspicion. Before claiming AI was used, consider if [Dunning–Kruger effect](https://en.wikipedia.org/wiki/Dunning%E2%80%93Kruger_effect "Dunning–Kruger effect") and [confirmation bias](https://en.wikipedia.org/wiki/Confirmation_bias "Confirmation bias") is clouding your judgement. Here are several somewhat commonly used indicators that are ineffective in LLM detection—and may even indicate the opposite.

- **Perfect grammar**: While modern LLMs are known for their high grammatical proficiency, many editors are also skilled writers or come from professional writing backgrounds. (See also [§ Discrepancies in writing style and variety of English](#discrepancies-in-writing-style-and-variety-of-english).)

- **"Bland" or "robotic" prose**: By default, modern LLMs tend toward effusive and verbose prose, as detailed above; while this tendency is formulaic, it may not scan as "robotic" to those unfamiliar with AI writing.[^14]

- **"Fancy," "academic," or unusual words**: While LLMs disproportionately favor certain words and phrases, many of which are long and have difficult readability scores, the correlation does not extend to *all* "fancy," academic, or "advanced"-sounding prose.[^1] Low-frequency and "unusual" words are also less likely to show up in AI-generated writing as they are statistically less common, unless they are proper nouns directly related to the topic.

- **Letter-like writing (in isolation)**: Although many talk page messages written with salutations, valedictions, subject lines, and other formalities after 2023 tend to appear AI-generated, letters and emails have conventionally been written in such ways *long* before modern LLMs existed. Human editors (particularly newer editors) may format their talk page comments similarly for various reasons, such as being more accustomed to formal communication, posting as part of a school assignment that requires such at one, or simply mistaking the talk page for email. AI-generated talk page messages tend to have other tells, such as vertical lists,[^d] placeholders, or abrupt cutoffs.

- **Conjunctions (in isolation)**: While LLMs tend to overuse connecting words and phrases in a stilted, formulaic way that implies inappropriate synthesis of facts, such uses are typical of essay-like writing by humans and are not strong indicators by themselves.

- **Bizarre wikitext**: While LLMs may hallucinate templates or generate wikitext code with invalid syntax for reasons explained in [§Use of Markdown](#use-of-markdown), they are not likely to generate content with certain random-seeming, "inexplicable" errors and artifacts (excluding the ones listed on this page in [§Markup](#markup)). Bizarrely placed HTML tags like `<span>` are more indicative of poorly programmed browser extensions or a known bug with Wikipedia's content translation tool (T113137). Misplaced syntax like `''Catch-22 i''s a satirical novel.` (rendered as "*Catch-22 i* s a satirical novel.") are more indicative of mistakes in VisualEditor, where such errors are harder to notice than in source editing.

---

## Notes

[^a]: not unique to AI chatbots; is produced by the {{as of}} template

[^b]: Example of `Would you like me to ... turn this into actual Wikipedia markup format (wikitext)?` in a deleted draft (administrators only)

[^c]: Example of ` ```wikitext ` on a draft.

[^d]: Example of a vertical list in a deletion discussion

---

## References

[^1]: Russell, Jenna; Karpinska, Marzena; Iyyer, Mohit (2025). [*People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text*](https://aclanthology.org/2025.acl-long.267/). Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Vienna, Austria: Association for Computational Linguistics. pp.5342–5373. arXiv:[2501.15654](https://arxiv.org/abs/2501.15654).

[^2]: Dugan, Liam; Hwang, Alyssa; Trhlik, Filip; Zhu, Andrew; Ludan, Josh Magnus; Xu, Hainiu; Ippolito, Daphne; Callison-Burch, Chris (2024). [*RAID: A Shared Benchmark for Robust Evaluation of Machine-Generated Text Detectors*](https://aclanthology.org/2024.acl-long.674). Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Bangkok, Thailand: Association for Computational Linguistics. pp.12463–12492. arXiv:[2405.07940](https://arxiv.org/abs/2405.07940).

[^3]: ["People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text"](https://arxiv.org/html/2501.15654v2). *arxiv.org*. Retrieved 2025-11-28.

[^4]: This can be directly observed by examining images generated by text-to-image models; they look acceptable at first glance, but specific details tend to be blurry and malformed. This is especially true for background objects and text.

[^5]: ["10 Ways AI Is Ruining Your Students' Writing"](https://www.chronicle.com/article/10-ways-ai-is-ruining-your-students-writing). *Chronicle of Higher Education*. September 16, 2025. Archived from the original on October 1, 2025. Retrieved October 1, 2025.

[^6]: Juzek, Tom S.; Ward, Zina B. (2025). [*Why Does ChatGPT "Delve" So Much? Exploring the Sources of Lexical Overrepresentation in Large Language Models*](https://aclanthology.org/2025.coling-main.426.pdf) (PDF). Findings of the Association for Computational Linguistics: ACL 2025. Association for Computational Linguistics. arXiv:[2412.11385](https://arxiv.org/abs/2412.11385).

[^7]: Reinhart, Alex; Markey, Ben; Laudenbach, Michael; Pantusen, Kachatad; Yurko, Ronald; Weinberg, Gordon; Brown, David West. ["Do LLMs write like humans? Variation in grammatical and rhetorical styles"](http://arxiv.org/abs/2410.16107). Retrieved 4 December 2025.

[^8]: Kobak, Dmitry; González-Márquez, Rita; Horvát, Emőke-Ágnes; Lause, Jan (2 July 2025). ["Delving into LLM-assisted writing in biomedical publications through excess vocabulary"](https://www.science.org/doi/10.1126/sciadv.adt3813). *Science Advances*. **11** (27). doi:[10.1126/sciadv.adt3813](https://doi.org/10.1126%2Fsciadv.adt3813). ISSN 2375-2548. PMC 12219543. PMID 40009654.

[^9]: Ju, Da; Blix, Hagen; Williams, Adina (2025). [*Domain Regeneration: How well do LLMs match syntactic properties of text domains?*](https://aclanthology.org/2025.findings-acl.120). Findings of the Association for Computational Linguistics: ACL 2025. Vienna, Austria: Association for Computational Linguistics. pp.2367–2388. arXiv:[2505.07784](https://arxiv.org/abs/2505.07784). doi:[10.18653/v1/2025.findings-acl.120](https://doi.org/10.18653%2Fv1%2F2025.findings-acl.120).

[^10]: Kousha, Kayvan; Thelwall, Mike (2025). [*How much are LLMs changing the language of academic papers after ChatGPT? A multi-database and full text analysis*](https://arxiv.org/pdf/2509.09596). ISSI 2025 Conference. arXiv:[2509.09596](https://arxiv.org/abs/2509.09596).

[^11]: Merrill, Jeremy B.; Chen, Szu Yu; Kumer, Emma (13 November 2025). ["What are the clues that ChatGPT wrote something? We analyzed its style"](https://www.washingtonpost.com/technology/interactive/2025/how-detect-chatgpt-em-dash/). *The Washington Post*. Retrieved 14 November 2025.

[^12]: ["Unproductive Interpretation of Work and Employment as Misinformation?"](https://www.laetusinpraesens.org/docs20s/workeco.php). Archived from the original on 2 September 2025. Retrieved 21 October 2025.

[^13]: See [T387903](https://phabricator.wikimedia.org/T387903 "phabricator:T387903").

[^14]: Murray, Nathan; Tersigni, Elisa (21 July 2024). ["Can instructors detect AI-generated papers? Postsecondary writing instructor knowledge and perceptions of AI"](https://journals.sfu.ca/jalt/index.php/jalt/article/view/1895). *Journal of Applied Learning & Teaching*. **7** (2). doi:[10.37074/jalt.2024.7.2.12](https://doi.org/10.37074%2Fjalt.2024.7.2.12). ISSN 2591-801X. Retrieved 21 November 2025.
