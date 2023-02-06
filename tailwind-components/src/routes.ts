import { Dataset, createPuppeteerRouter } from "crawlee";

export const router = createPuppeteerRouter();

router.addDefaultHandler(async ({ enqueueLinks, log }) => {
    log.info(`enqueueing new URLs`);
    await enqueueLinks({
        globs: ["https://tailwindcomponents.com/component/*"],
        label: "detail",
    });
    await enqueueLinks({
        globs: ["https://tailwindcomponents.com/components/*"],
        label: "listing",
    });
});

router.addHandler("detail", async ({ request, page, log }) => {
    log.info(`Crawling Details`, {
        url: request.loadedUrl,
    });

    await page.waitForSelector("html");
    const data = await page.evaluate(() => {
        const description =
            document.querySelector("p.description-link")!.innerHTML;
        const code = document
            .querySelector("iframe")!
            .contentDocument!.querySelector("html")!
            .querySelector("body")!;

        var scripts = code.getElementsByTagName("script");
        var i = scripts.length;
        while (i--) {
            scripts[i].parentNode!.removeChild(scripts[i]);
        }

        return {
            html: code.innerHTML.trim(),
            desc: description,
        };
    });

    log.info(`Pushing data to dataset`, {
        desc: data.desc,
        url: request.loadedUrl,
    });
    await Dataset.pushData({
        html: data.html,
        desc: data.desc,
        url: request.loadedUrl,
    });
});

router.addHandler("listing", async ({ enqueueLinks, request, page, log }) => {
    const title = await page.title();
    log.info(`${title}`, { url: request.loadedUrl });

    await enqueueLinks({
        globs: ["https://tailwindcomponents.com/component/*"],
        label: "detail",
    });
});
