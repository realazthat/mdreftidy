# Example markdown file

## Non reference link

A link to a local file [LICENSE](./non-reference-local-link).

## Reference link: In order

A link to a local file [Reference link: In order][1].

## Reference link: Out of order

A link to a local file [Reference link: Out of order 1][2].

A link to a local file [Reference link: Out of order 2][3].

## Reference link: Out of order, inline references

A link to a local file [Reference link: Out of order, inline references 1][4].

A link to a local file [Reference link: Out of order, inline references 2][5].

[4]: ./reference-link-out-of-order-1
[5]: ./reference-link-out-of-order-2

## Reference image: Out of order, inline references

An image ![Reference image: Out of order, inline references 1][6].

An image ![Reference image: Out of order, inline references 2][7].

[6]: ./reference-image-out-of-order-1
[7]: ./reference-image-out-of-order-2

## Footnotes

Note how the footnootes are out of order:

[8]: ./unused-reference-link
[2]: ./reference-link-out-of-order-1
[1]: ./reference-link-in-order
[3]: ./reference-link-out-of-order-2
