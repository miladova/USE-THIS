import pathlib, re

root = pathlib.Path(__file__).parent
chaps = sorted((root / "chapters").glob("*.md"))

titles = []
for p in chaps:
    first = p.read_text(encoding="utf-8").splitlines()
    num = first[0].lstrip("# ").strip()
    name = first[2].lstrip("# ").strip()
    titles.append((num, name))

front = """<div align="center">

# THE FIFTH OFFICER

### A Novella of the *Titanic*

</div>

---

> *"I am a seaman."*
>
> — Harold Godfrey Lowe, Fifth Officer, R.M.S. *Titanic*,
> before the United States Senate Inquiry, April 1912

---

<div align="center">

*For everyone who has ever said a thing twelve years too late*

</div>

---

**Contents**

"""

for num, name in titles:
    front += f"- **{num}** · {name}\n"

front += """
---

*This is a work of fiction. Arwen Prys Vaughan, her family, and the passengers and crew who surround her at close range are invented. Harold Godfrey Lowe was a real man and the ship was a real ship; where the record is firm I have tried to be faithful to it, and where the record is silent I have imagined. The officers of the* Titanic *— Smith, Wilde, Murdoch, Lightoller, Pitman, Boxhall, Lowe, Moody — were eight men on a ship built to be unsinkable. Four of them lived.*

---
"""

parts = [front]
for p in chaps:
    body = p.read_text(encoding="utf-8").strip()
    parts.append(body + "\n\n---\n")

parts.append("""<div align="center">

***THE END***

</div>

---

### A note on the record

Harold Godfrey Lowe (1882–1944) was born at Eglwys Fach in Merionethshire and went to sea at fourteen. He was twenty-nine when he served as Fifth Officer of the *Titanic*. He was in charge of Lifeboat No. 14, and after the ship went down he took his boat back into the wreckage — the only officer to do so — and picked survivors out of the water and off the swamped Collapsible A. He fired three warning shots into the air to hold back a rush on his boat, and he was criticised for his language in doing it; asked at the American inquiry whether he was a seaman, he replied that he was. He went back to sea, served in the Royal Naval Reserve through the war, and died at Deganwy in 1944.

The ship was 882 feet long and 46,000 tons gross, and she carried sixteen lifeboats and four collapsibles, with a total capacity of 1,178 persons, for 2,208 people. She struck the ice at 11.40 p.m. on 14 April 1912 and sank at 2.20 a.m. on 15 April. Seven hundred and five people were saved by the *Carpathia*.

Everything else in this book — the woman with the pheasant in her hat, the steward who was sure it was a bit of machinery, the tin cup of coffee at six o'clock in the morning — is invented, and is offered with respect.
""")

out = root / "The-Fifth-Officer.md"
out.write_text("\n".join(parts), encoding="utf-8")
words = len(re.findall(r"\S+", out.read_text(encoding="utf-8")))
print(f"wrote {out} — {words:,} words")
