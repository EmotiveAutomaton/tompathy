import { openReview } from "./chrome-review.mjs";

try {
  const review = await openReview();
  console.log(
    `\nToMpathy review is ready in Google Chrome ${review.receipt.chromeVersion}.\n` +
      `${review.receipt.action} · version ${review.receipt.version} · build ${review.receipt.build}\n` +
      (review.receipt.readingLeftOpen
        ? "Your current reading has been left open.\n"
        : "") +
      `Bookmark the review page in this Chrome profile:\n${review.receipt.reviewUrl}\n\n` +
      "No terminal or local server needs to stay open.\n" +
      "After code changes, run Review ToMpathy.cmd again.\n",
  );
  await review.browser.close(); // Disconnect; the owner's Chrome stays open.
} catch (error) {
  console.error(`\nReview setup failed: ${error.message}\n`);
  process.exitCode = 1;
}
