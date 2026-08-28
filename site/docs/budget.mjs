// The area's own budget (RK1409), in the shape `[budgets]` already uses one file over: a
// default, plus a named entry per page that needs its own number, and the argument for each
// written above the key rather than in a commit message nobody will find.
//
// **Why an area needs one at all.** The measurement that started this project is what an
// unbounded prose file costs — an index that reached 186 KB while declaring itself an index, a
// rationale file at 539 KB while scoped to unshipped work. A documentation area is that same
// invitation with better typography: every page has room, nothing refuses a paragraph, and the
// author who diagnoses the drift is usually the one who wrote most of it.
//
// What this buys is what the write path buys. It is not a lint about prose quality — nothing
// here reads an English sentence. It is a number a build checks, and its value is that the
// question "what would I cut?" never arrives, because the ceiling was known before the first
// sentence was composed to fill it.

// The default, measured rather than picked. Eleven pages existed when this was declared; the
// ten that are not the model page ran 240–595 words, p90 524, and 600 is the first round
// number above that. Deliberately not the maximum: a ceiling set at whatever the longest page
// happens to be refuses nothing on the day it is written, which is how "under 150 lines" ends
// up describing 20 KB.
export const WORDS = 600;

// Pages with their own number, each argued. A page here is a decision somebody made, not a
// page that grew — which is the difference between an exception and an exemption.
export const PAGES = {
  // The model page is a glossary of one system, and its length is what buys every other page
  // theirs: the six reference pages average 276 words *because* they link here instead of
  // saying what a block is before they can say what the verb does. Splitting it would file one
  // system under six headings, which is the state RK1407 was written to end. Measured at 1249
  // when this was declared, so the number is the first round hundred above it.
  "model.mdx": 1300,
};

// Pages the build writes, which are counted and reported apart. A verb page's table is as long
// as the parser makes it, and cutting it would be editing a schema to fit a budget — so the
// budget is over the prose an author wrote, and this is how the counter is told which is which.
export const GENERATED = ["findings"];
