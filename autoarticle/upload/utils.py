def create_image_tag(responce_json: dict):
    return (
        r"""
    <figure class="wp-block-image size-large">
      <img
        fetchpriority="high"
        decoding="async"
        width="1024"
        height="546"
        src="{large}"
        alt="{alt}"
        class="wp-image"
        srcset="
          {large}        1024w,
          {medium}        300w,
          {thumbnail}     150w,
          {medium_large}  768w,
          {1536x1536}    1536w,
          {2048x2048}    2048w
        "
        sizes="(max-width: 1024px) 100vw, 1024px"
      />
    </figure>
    """.replace(
            r"{large}", responce_json["media_details"]["sizes"]["large"]["source_url"]
        )
        .replace(
            r"{medium}", responce_json["media_details"]["sizes"]["medium"]["source_url"]
        )
        .replace(
            r"{thumbnail}",
            responce_json["media_details"]["sizes"]["thumbnail"]["source_url"],
        )
        .replace(
            r"{medium_large}",
            responce_json["media_details"]["sizes"]["medium_large"]["source_url"],
        )
        .replace(
            r"{1536x1536}",
            responce_json["media_details"]["sizes"]["1536x1536"]["source_url"],
        )
        .replace(
            r"{2048x2048}",
            responce_json["media_details"]["sizes"]["2048x2048"]["source_url"],
        )
    ).replace(r"{alt}", responce_json["alt_text"])


def trim_newlines(input_str):
    # Find the index of the first non-newline character
    start_index = 0
    while start_index < len(input_str) and input_str[start_index] == "\n":
        start_index += 1

    # Find the index of the last non-newline character
    end_index = len(input_str) - 1
    while end_index >= 0 and input_str[end_index] == "\n":
        end_index -= 1

    # Return the trimmed string
    return input_str[start_index : end_index + 1]
