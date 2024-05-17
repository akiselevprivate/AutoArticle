# AUTOARTICLE

A cli tool for creating AI articles with interlinking, image generation, product listicles, etc.

# How to Use

```
python autoarticle create config articles.csv "[[30, 1], [1, 20]]" # a 2d list of [number of articles, days]

python autoarticle create collections config.json (-ot for only titles, saved in titles.txt)

python autoarticle create existing (use this only if used -ot in the previous step)

python autoarticle generate (all/#of colleciton)

python autoarticle upload shuffle (#of collection) start_date end_date (date format eg. 2024-05-01)

python autoarticle upload schedule (#of starting collection eg. 2) starting_date

python autoarticle upload collection (#of collection)
```
