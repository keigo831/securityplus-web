import docx, re, json, html, argparse, os

def extract_keywords(text, n=3):
    stopwords=set("""the and for with that this which from into to be of in on at by is an or as most likely being have has are will would should could can may might if only but not who whom than then so such a an any etc following using before use used other""".split())
    words = re.findall(r"[A-Za-z']{4,}", text.lower())
    keywords=[]
    for w in words:
        if w not in stopwords and w not in keywords:
            keywords.append(w)
        if len(keywords)==n:
            break
    return keywords

def parse_block(block):
    lines = block.strip().splitlines()
    question_lines=[]
    options=[]
    correct=None
    explanation=[]
    for line in lines:
        if re.match(r'[A-D]\.', line.strip()):
            options.append(line.strip())
        elif line.startswith("Correct Answer"):
            correct=line.split(":")[1].strip()
        elif not options:
            question_lines.append(line)
        else:
            explanation.append(line)
    question_text="\n".join(question_lines)
    return question_text, options, correct, "\n".join(explanation)

def create_question_obj(num, block):
    qtext, options, correct_letter, explanation = parse_block(block)
    kws = extract_keywords(qtext, 3)
    qhtml = qtext
    for kw in kws:
        pattern = re.compile(re.escape(kw), re.I)
        qhtml = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", qhtml, 1)
    qhtml = html.escape(qhtml).replace("\n", "<br>")
    ans_option = next((opt for opt in options if opt.startswith(correct_letter + ".")), "")
    ans_text = ans_option.split(". ", 1)[1] if ". " in ans_option else ""
    return {
        "id": num,
        "question_html": qhtml,
        "options": [html.escape(o) for o in options],
        "correct_letter": correct_letter,
        "correct_text": html.escape(ans_text),
        "keywords": kws,
        "keywords_cn": ["" for _ in kws],
        "answer_cn": "",
        "explanation_cn": ""
    }

def main(docx_path, output_json):
    with docx.Document(docx_path) as doc:
        texts = [p.text for p in doc.paragraphs]
    full_text = "\n".join(texts)
    pattern = re.compile(r'Question #(\d+)\n(.*?)(?=\nQuestion #\d+\n|\Z)', re.S)
    data=[]
    for m in pattern.finditer(full_text):
        num = int(m.group(1))
        block = m.group(2).strip()
        data.append(create_question_obj(num, block))
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(data)} questions to {output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse SY0-701 docx to questions.json")
    parser.add_argument("docx", help="Input DOCX file containing questions")
    parser.add_argument("-o","--output", default="questions.json")
    args = parser.parse_args()
    main(args.docx, args.output)