import { nav } from "../lib/site-content";
import { Mark } from "./ui/Mark";

// The bar is anchors into this one page plus one link that leaves it — /roadkeep/docs/ is a
// second build under the same base, so it is written as a path and there is no route for it in
// routes.tsx. Below 900px the labels give way and the GitHub button is what is left, which is
// why that button is the only entry here that is not also in the footer.
export function Nav() {
  return (
    <nav>
      <div className="wrap">
        <div className="nav-left">
          <a className="brand" href="#top">
            <Mark />
            {nav.brand}
          </a>
          <a className="parent" href={nav.parent.href} title="alegauss — small developer tools">
            <span className="pre">{nav.parent.pre}</span>
            <b>{nav.parent.name}</b>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M7 17 17 7" />
              <path d="M9 7h8v8" />
            </svg>
          </a>
        </div>
        <div className="nav-links">
          {nav.links.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
          <a className="btn btn-primary btn-sm" href={nav.cta.href}>
            {nav.cta.label}
          </a>
        </div>
      </div>
    </nav>
  );
}
