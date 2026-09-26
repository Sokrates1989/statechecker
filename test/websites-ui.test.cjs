const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const websiteRoot = path.resolve(__dirname, '..', 'website');
const exampleUrl = 'https://websiteToTest.com';
const peerUrl = 'https://api.peer.example/health';

function loadBrowser(language = 'en-US') {
    const classes = new Set(['hidden']);
    const guidance = {
        textContent: '',
        lang: '',
        classList: {
            toggle(name, force) {
                if (force) classes.add(name);
                else classes.delete(name);
            },
            contains(name) {
                return classes.has(name);
            }
        }
    };
    const list = { innerHTML: '' };
    const statuses = [];
    let confirmations = 0;
    const browser = vm.createContext({
        window: {},
        navigator: { language },
        document: {
            getElementById(id) {
                return {
                    'website-examples-guidance': guidance,
                    'websites-list': list
                }[id] || null;
            }
        },
        URL,
        confirm() {
            confirmations += 1;
            return true;
        },
        showStatus(message, type = 'success') {
            statuses.push({ message, type });
        }
    });

    for (const relativePath of ['locales/en.js', 'locales/de.js', 'i18n.js', 'websites/websites.js']) {
        vm.runInContext(fs.readFileSync(path.join(websiteRoot, relativePath), 'utf8'), browser);
    }

    return {
        browser,
        guidance,
        list,
        statuses,
        get confirmations() {
            return confirmations;
        }
    };
}

test('new UI messages have matching English and German catalogs', () => {
    const { browser } = loadBrowser('de-DE');
    const catalogs = browser.window.STATECHECKER_MESSAGES;
    assert.deepEqual(Object.keys(catalogs.de).sort(), Object.keys(catalogs.en).sort());
    assert.equal(browser.window.statecheckerLocale, 'de');
    assert.match(browser.window.statecheckerT('websites.removed', { url: peerUrl }), /Website.*entfernt/);
    assert.equal(loadBrowser('fr-FR').browser.window.statecheckerLocale, 'en');
});

test('example-only list explains the prerequisite and does not submit a delete', async () => {
    const ui = loadBrowser();
    ui.browser.window.websitesData = [{ url: exampleUrl }, { url: 'http://websiteToTest.com' }];
    ui.browser.renderWebsites();
    assert.equal(ui.guidance.classList.contains('hidden'), false);
    assert.match(ui.guidance.textContent, /Add a website you want to monitor before removing them/);

    let deleteCalls = 0;
    ui.browser.apiCall = async () => { deleteCalls += 1; };
    await ui.browser.removeWebsite(exampleUrl);

    assert.equal(deleteCalls, 0);
    assert.equal(ui.confirmations, 0);
    assert.equal(ui.statuses.at(-1).type, 'warning');
});

test('after adding a peer, removing an example refreshes before reporting success', async () => {
    const ui = loadBrowser();
    ui.browser.window.websitesData = [{ url: exampleUrl }, { url: peerUrl }];
    ui.browser.renderWebsites();
    assert.equal(ui.guidance.classList.contains('hidden'), true);

    const calls = [];
    ui.browser.apiCall = async (endpoint, method, body) => { calls.push({ endpoint, method, body }); };
    ui.browser.apiCallWithAuthCheck = async () => ({ websites: [{ url: peerUrl }] });
    await ui.browser.removeWebsite(exampleUrl);

    assert.equal(calls.length, 1);
    assert.equal(calls[0].method, 'DELETE');
    assert.equal(calls[0].body.url, exampleUrl);
    assert.equal(ui.statuses.at(-1).type, 'success');
    assert.match(ui.statuses.at(-1).message, /removed/);
    assert.equal(ui.browser.window.websitesData.length, 1);
});

test('a URL still returned by the API is not reported as removed', async () => {
    const ui = loadBrowser();
    ui.browser.window.websitesData = [{ url: exampleUrl }, { url: peerUrl }];
    ui.browser.apiCall = async () => ({});
    ui.browser.apiCallWithAuthCheck = async () => ({
        websites: [{ url: exampleUrl }, { url: peerUrl }]
    });

    await ui.browser.removeWebsite(exampleUrl);

    assert.equal(ui.statuses.at(-1).type, 'warning');
    assert.match(ui.statuses.at(-1).message, /still being watched/);
    assert.equal(ui.statuses.some(({ type }) => type === 'success'), false);
});
