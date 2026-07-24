#!/usr/bin/env node

const targetAvatarId = process.argv[2];
const debugPort = process.env.CODEX_REMOTE_DEBUGGING_PORT || "9341";

if (!targetAvatarId) {
  console.error("用法：select_codex_pet.mjs custom:<pet-id>");
  process.exit(1);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function getPages() {
  const response = await fetch(`http://127.0.0.1:${debugPort}/json/list`);
  if (!response.ok) {
    throw new Error(`Codex 调试端口返回 ${response.status}`);
  }
  return await response.json();
}

async function getMainPage() {
  const targets = await getPages();
  return targets.find(
    (target) =>
      target.type === "page" &&
      target.url === "app://-/index.html" &&
      target.webSocketDebuggerUrl,
  );
}

async function reloadAvatarOverlay() {
  const targets = await getPages();
  const overlay = targets.find(
    (target) =>
      target.type === "page" &&
      target.url.includes("initialRoute=%2Favatar-overlay") &&
      target.webSocketDebuggerUrl,
  );
  if (!overlay) return false;
  await new Promise((resolve, reject) => {
    const socket = new WebSocket(overlay.webSocketDebuggerUrl);
    const timeout = setTimeout(() => {
      socket.close();
      reject(new Error("刷新 Codex 宠物浮窗超时"));
    }, 8000);
    socket.addEventListener("open", () => {
      socket.send(JSON.stringify({ id: 1, method: "Page.reload" }));
    });
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (message.id !== 1) return;
      clearTimeout(timeout);
      socket.close();
      resolve();
    });
    socket.addEventListener("error", () => {
      clearTimeout(timeout);
      reject(new Error("无法刷新 Codex 宠物浮窗"));
    });
  });
  return true;
}

async function evaluateInPage(webSocketDebuggerUrl, expression) {
  return await new Promise((resolve, reject) => {
    const socket = new WebSocket(webSocketDebuggerUrl);
    const commandId = 1;
    const timeout = setTimeout(() => {
      socket.close();
      reject(new Error("等待 Codex 页面响应超时"));
    }, 15000);

    socket.addEventListener("open", () => {
      socket.send(
        JSON.stringify({
          id: commandId,
          method: "Runtime.evaluate",
          params: {
            expression,
            awaitPromise: true,
            returnByValue: true,
          },
        }),
      );
    });

    socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (message.id !== commandId) return;
      clearTimeout(timeout);
      socket.close();
      if (message.error) {
        reject(new Error(message.error.message));
        return;
      }
      if (message.result?.exceptionDetails) {
        reject(
          new Error(
            message.result.exceptionDetails.exception?.description ||
              message.result.exceptionDetails.text ||
              "Codex 页面脚本执行失败",
          ),
        );
        return;
      }
      resolve(message.result?.result?.value);
    });

    socket.addEventListener("error", () => {
      clearTimeout(timeout);
      reject(new Error("无法连接 Codex 页面"));
    });
  });
}

function buildSelectionExpression(avatarId) {
  return `(() => {
    const avatarId = ${JSON.stringify(avatarId)};
    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (finder, timeoutMs = 5000) => {
      const startedAt = Date.now();
      while (Date.now() - startedAt < timeoutMs) {
        const value = finder();
        if (value) return value;
        await delay(80);
      }
      return null;
    };
    const buttonText = (button) => (button?.innerText || "").trim();
    const findButton = (patterns) =>
      [...document.querySelectorAll("button")].find((button) => {
        const values = [
          buttonText(button),
          button.getAttribute("aria-label") || "",
          button.getAttribute("title") || "",
        ];
        return patterns.some((pattern) =>
          values.some((value) => pattern.test(value)),
        );
      });
    const findMenuItem = (patterns) =>
      [...document.querySelectorAll('[role="menuitem"]')].find((item) => {
        const value = (item.innerText || "").trim();
        return patterns.some((pattern) => pattern.test(value));
      });
    const findCard = () => document.querySelector('[data-avatar-id="' + avatarId + '"]');
    const findCardAction = (card) => {
      let node = card;
      while (node && node !== document.body) {
        const buttons = [...node.querySelectorAll("button")];
        const action = buttons.find((button) =>
          /^(选择|已选|Select|Selected)$/.test(buttonText(button)),
        );
        if (action) return action;
        node = node.parentElement;
      }
      return null;
    };

    return (async () => {
      let openedSettings = false;
      let card = findCard();

      if (!card) {
        let petButton = findButton([/^宠物$/, /^Pets?$/i]);
        if (!petButton) {
          const profileButton =
            document.querySelector('button[aria-label="打开个人资料菜单"]') ||
            document.querySelector('button[aria-label*="profile menu" i]');
          if (!profileButton) {
            const diagnostics = [...document.querySelectorAll("button")]
              .slice(0, 40)
              .map((button) => ({
                text: buttonText(button),
                aria: button.getAttribute("aria-label") || "",
                title: button.getAttribute("title") || "",
              }));
            throw new Error(
              "找不到 Codex 个人资料菜单；当前按钮：" +
                JSON.stringify(diagnostics),
            );
          }
          profileButton.click();
          const settingsItem = await waitFor(() =>
            findMenuItem([/^设置/, /^Settings$/i]),
          );
          if (!settingsItem) throw new Error("找不到 Codex 设置");
          settingsItem.click();
          openedSettings = true;
          petButton = await waitFor(() => findButton([/^宠物$/, /^Pets?$/i]));
        }
        if (!petButton) throw new Error("找不到 Codex 宠物设置");
        petButton.click();
        await delay(250);
        const initialRefreshButton = findButton([/^刷新$/, /^Refresh$/i]);
        if (initialRefreshButton) {
          initialRefreshButton.click();
          await delay(500);
        }
        card = await waitFor(findCard);
      }

      if (!card) throw new Error("Codex 未发现目标宠物：" + avatarId);
      const refreshButton = findButton([/^刷新$/, /^Refresh$/i]);
      if (refreshButton) {
        refreshButton.click();
        await delay(350);
        card = await waitFor(findCard);
      }
      const action = findCardAction(card);
      if (!action) throw new Error("找不到目标宠物的选择按钮");

      const wasSelected = /^(已选|Selected)$/.test(buttonText(action));
      if (!wasSelected) {
        action.click();
        await waitFor(() => {
          const currentCard = findCard();
          const currentAction = currentCard ? findCardAction(currentCard) : null;
          return currentAction && /^(已选|Selected)$/.test(buttonText(currentAction));
        });
      }

      if (openedSettings) {
        const backButton = findButton([/^返回应用$/, /^Back to app$/i]);
        backButton?.click();
      }
      return { avatarId, selected: true, changed: !wasSelected };
    })();
  })()`;
}

try {
  const page = await getMainPage();
  if (!page) {
    throw new Error(`没有在 127.0.0.1:${debugPort} 找到 Codex 主窗口`);
  }
  const result = await evaluateInPage(
    page.webSocketDebuggerUrl,
    buildSelectionExpression(targetAvatarId),
  );
  await reloadAvatarOverlay();
  console.log(JSON.stringify(result));
} catch (error) {
  console.error(`实时刷新未完成：${error.message}`);
  process.exit(2);
}
