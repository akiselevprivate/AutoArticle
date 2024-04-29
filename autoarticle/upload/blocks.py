import random

PRODUCT_REVIEW_2_TEMPLATE = open(
    "autoarticle/upload/templates/product-review-2.html"
).read()

PRODUCT_LIST_ITEM_TEMPLATE = open(
    "autoarticle/upload/templates/product-group-item.txt"
).read()

PRODUCT_LIST_GROUP_TEMPLATE = open(
    "autoarticle/upload/templates/product-group.html"
).read()


def product_review_2_block(
    title: str,
    rating: float,
    description: str,
    pros: list[str],
    cons: list[str],
    img_src: str,
    img_alt: str,
    button_names: list[str],
    button_urls: list[str],
):
    buttons_html = []
    for name, url in zip(button_names, button_urls):
        button_html = f'<a href="{url}" target="_self" rel="noopener" class="afpb__btn afpb__btn_7e4ed4ad" style="color:#ffffff;background-color:#d59215;border:0px solid #d59215;border-radius:0px">{name}</a>'
        buttons_html.append(button_html)

    buttons_html = "".join(buttons_html)

    pros_list = ["<ul>"]
    cons_list = ["<ul>"]
    for p in pros:
        pros_list.append(f"<li>{p}</li>")
    for c in cons:
        cons_list.append(f"<li>{c}</li>")

    pros_list.append("</ul>")
    pros_list = "".join(pros_list)
    cons_list.append("</ul>")
    cons_list = "".join(cons_list)

    html = (
        PRODUCT_REVIEW_2_TEMPLATE.replace(r"{{title}}", title)
        .replace(r"{{rating}}", str(rating))
        .replace(r"{{description}}", description)
        .replace(r"{{pros_list}}", pros_list)
        .replace(r"{{cons_list}}", cons_list)
        .replace(r"{{img_src}}", img_src)
        .replace(r"{{img_alt}}", img_alt)
        .replace(r"{{buttons}}", buttons_html)
    )

    return html


def create_product_item(
    title: str,
    rating: str,
    description: str,
    img_src: str,
    img_alt: str,
    button_name: str,
    button_url: str,
):
    prod_id = str(random.randint(100000, 999999))

    html = (
        PRODUCT_LIST_ITEM_TEMPLATE.replace(r"{{id}}", prod_id)
        .replace(r"{{title}}", title)
        .replace(r"{{rating}}", str(rating))
        .replace(r"{{description}}", description)
        .replace(r"{{img_src}}", img_src)
        .replace(r"{{img_alt}}", img_alt)
        .replace(r"{{button_url}}", button_url)
        .replace(r"{{button}}", button_name)
    )

    return html


def create_product_group(product_items_htmls: list[str]):
    items_html = "".join(product_items_htmls)

    html = PRODUCT_LIST_GROUP_TEMPLATE.replace(r"{{products}}", items_html)

    return html


product_item = create_product_item(
    "Gaming PC 1",
    4.5,
    "Cool Description",
    "http://localhost/wp-content/uploads/2024/04/avatar-9.png",
    "",
    "$700 on amazon",
    "https://google.com/",
)

open("test.html", "w+").write(create_product_group([product_item, product_item]))
