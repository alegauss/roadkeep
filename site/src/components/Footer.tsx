import { footer, sponsor } from "../lib/site-content";
import { Mark } from "./ui/Mark";

// The sponsor block is rendered markup rather than a runtime fetch, on purpose: a block drawn
// after load is one the crawlers and the models reading this page never see, and the sponsor
// is the reason the page can be free of anything else. Its data is generated into the content
// module from alegauss.github.io/sponsor.json — edit the JSON, not this file.
export function Footer() {
  return (
    <footer>
      <div className="wrap">
        <div className="foot-grid">
          <a className="foot-brand" href="#top">
            <Mark />
            {footer.brand}
          </a>
          <div className="foot-links">
            {footer.links.map((link) => (
              <a key={link.href} href={link.href}>
                {link.label}
              </a>
            ))}
          </div>
        </div>

        <div className="sponsor">
          <img
            className="sponsor-mark"
            src={sponsor.mark.src}
            alt={sponsor.mark.alt}
            width={42}
            height={42}
            loading="lazy"
            decoding="async"
          />
          <div className="sponsor-body">
            <span className="sponsor-label">{sponsor.label}</span>
            <a
              className="sponsor-name"
              href={sponsor.href}
              target="_blank"
              rel="noopener"
            >
              {sponsor.name}
            </a>
            <p>
              {sponsor.blurbLead}
              <a href={sponsor.blurbLink.href} target="_blank" rel="noopener">
                {sponsor.blurbLink.label}
              </a>
              .
            </p>
            <div className="sponsor-products">
              {sponsor.products.map((product) => (
                <a
                  className="sponsor-product"
                  key={product.href}
                  href={product.href}
                  target="_blank"
                  rel="noopener"
                >
                  <img
                    src={product.src}
                    alt={product.alt}
                    width={28}
                    height={28}
                    loading="lazy"
                    decoding="async"
                  />
                  <span>
                    <b>{product.name}</b>
                    <small>{product.note}</small>
                  </span>
                </a>
              ))}
            </div>
          </div>
        </div>

        <p className="disclaimer">{footer.disclaimer}</p>
      </div>
    </footer>
  );
}
