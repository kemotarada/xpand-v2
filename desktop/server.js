// ======================================================
// KEMO DESKTOP BRIDGE V2.1
//
// REALTIME WHOLE-PC BRIDGE
//
// Railway <-> Persistent WebSocket <-> Windows PC
//
// Supports:
// - Legacy mouse/keyboard/screenshot commands
// - Chrome CDP direct commands
// - Windows UI Automation
// - Window foreground control
// - Installed application launching
//
// Safety:
// - Explicit allowlist only
// - No arbitrary shell execution
// ======================================================

import express from "express";
import crypto from "node:crypto";
import http from "node:http";

import {
  WebSocketServer,
  WebSocket
} from "ws";


// ======================================================
// ENV
// ======================================================

const PORT = Number(
  process.env.PORT || 3000
);

const KEMO_DESKTOP_KEY = String(
  process.env.KEMO_DESKTOP_KEY || ""
).trim();

const KEMO_DESKTOP_DEVICE_ID = String(
  process.env.KEMO_DESKTOP_DEVICE_ID || "main-pc"
).trim();


// ======================================================
// SETTINGS
// ======================================================

const AGENT_ONLINE_MS = 30000;

const SYNC_COMMAND_TIMEOUT_MS = 30000;

const MAX_QUEUE = 100;

const RESULT_RETENTION_MS =
  30 * 60 * 1000;


// ======================================================
// EXPRESS
// ======================================================

const app = express();

app.disable(
  "x-powered-by"
);

app.use(
  express.json({
    limit: "24mb"
  })
);


// ======================================================
// HTTP SERVER
// ======================================================

const server =
  http.createServer(app);


// ======================================================
// WEBSOCKET SERVER
// ======================================================

const wss =
  new WebSocketServer({
    noServer: true
  });


// ======================================================
// MEMORY
// ======================================================

const commandQueue = [];

const commands =
  new Map();

const commandResults =
  new Map();

const resultWaiters =
  new Map();

let realtimeAgent = null;

let lastAgentSeenAt = null;

let lastAgentInfo = null;


// ======================================================
// HELPERS
// ======================================================

function cleanText(
  value,
  maxLength = 4000
) {
  return String(
    value ?? ""
  )
    .replace(/\u0000/g, "")
    .trim()
    .slice(
      0,
      maxLength
    );
}


function nowIso() {
  return new Date()
    .toISOString();
}


function createCommandId() {
  return crypto.randomUUID();
}


function safeEqual(
  a,
  b
) {
  const first =
    Buffer.from(
      String(a || "")
    );

  const second =
    Buffer.from(
      String(b || "")
    );

  if (
    first.length === 0
    ||
    first.length !== second.length
  ) {
    return false;
  }

  return crypto.timingSafeEqual(
    first,
    second
  );
}


function getProvidedKey(
  req
) {
  return cleanText(
    req.headers[
      "x-kemo-desktop-key"
    ],
    1000
  );
}


function requireDesktopKey(
  req,
  res,
  next
) {
  if (
    !KEMO_DESKTOP_KEY
  ) {
    return res
      .status(503)
      .json({
        ok: false,
        error:
          "KEMO_DESKTOP_KEY is not configured"
      });
  }

  if (
    !safeEqual(
      getProvidedKey(req),
      KEMO_DESKTOP_KEY
    )
  ) {
    return res
      .status(401)
      .json({
        ok: false,
        error:
          "Unauthorized"
      });
  }

  next();
}


function agentOnline() {
  if (
    !lastAgentSeenAt
  ) {
    return false;
  }

  const seen =
    new Date(
      lastAgentSeenAt
    ).getTime();

  if (
    !Number.isFinite(
      seen
    )
  ) {
    return false;
  }

  return (
    Date.now() - seen
    <
    AGENT_ONLINE_MS
  );
}


function websocketOnline() {
  return Boolean(
    realtimeAgent
    &&
    realtimeAgent.readyState
    ===
    WebSocket.OPEN
  );
}


// ======================================================
// ALLOWED ACTIONS
// ======================================================

const ALLOWED_ACTIONS =
  new Set([

    // ================================================
    // BASIC WINDOWS
    // ================================================

    "status",
    "screenshot",
    "open_app",
    "open_url",
    "find_file",

    // ================================================
    // MOUSE
    // ================================================

    "get_cursor",
    "mouse_move",
    "mouse_click",
    "mouse_double_click",
    "mouse_right_click",
    "mouse_scroll",

    // ================================================
    // KEYBOARD
    // ================================================

    "type_text",
    "press_key",
    "hotkey",

    // ================================================
    // CHROME DIRECT / CDP
    // ================================================

    "browser_status",
    "browser_snapshot",
    "browser_execute",

    // ================================================
    // WINDOWS WHOLE-PC DIRECT
    // ================================================

    "window_list",
    "window_activate",
    "open_installed_app",

    "uia_snapshot",
    "uia_execute"
  ]);


// ======================================================
// FINALIZE COMMAND
// ======================================================

function finalizeCommand(
  commandId,
  status,
  result
) {
  const existing =
    commandResults.get(
      commandId
    );

  if (
    !existing
  ) {
    return false;
  }

  const finalStatus =
    status === "failed"
      ?
      "failed"
      :
      "completed";

  const record = {
    ...existing,

    status:
      finalStatus,

    result:
      result ?? null,

    completedAt:
      nowIso()
  };

  commandResults.set(
    commandId,
    record
  );

  const command =
    commands.get(
      commandId
    );

  if (
    command
  ) {
    command.status =
      finalStatus;
  }

  const waiter =
    resultWaiters.get(
      commandId
    );

  if (
    waiter
  ) {
    clearTimeout(
      waiter.timer
    );

    resultWaiters.delete(
      commandId
    );

    waiter.resolve(
      record
    );
  }

  return true;
}


// ======================================================
// CREATE COMMAND
// ======================================================

function createCommand(
  action,
  args,
  deviceId
) {
  if (
    !ALLOWED_ACTIONS.has(
      action
    )
  ) {
    throw new Error(
      "Action is not allowed"
    );
  }

  if (
    deviceId !==
    KEMO_DESKTOP_DEVICE_ID
  ) {
    throw new Error(
      "Unknown device"
    );
  }

  const command = {
    id:
      createCommandId(),

    deviceId,

    action,

    args:
      (
        args
        &&
        typeof args === "object"
        &&
        !Array.isArray(args)
      )
        ?
        args
        :
        {},

    status:
      "created",

    createdAt:
      nowIso()
  };

  commands.set(
    command.id,
    command
  );

  commandResults.set(
    command.id,
    {
      id:
        command.id,

      action:
        command.action,

      status:
        "created",

      createdAt:
        command.createdAt,

      result:
        null
    }
  );

  return command;
}


// ======================================================
// DISPATCH COMMAND
// ======================================================

function dispatchCommand(
  command
) {
  if (
    websocketOnline()
  ) {
    command.status =
      "running";

    command.startedAt =
      nowIso();

    command.transport =
      "websocket";

    commandResults.set(
      command.id,
      {
        id:
          command.id,

        action:
          command.action,

        status:
          "running",

        createdAt:
          command.createdAt,

        startedAt:
          command.startedAt,

        transport:
          "websocket",

        result:
          null
      }
    );

    realtimeAgent.send(
      JSON.stringify({
        type:
          "command",

        command: {
          id:
            command.id,

          action:
            command.action,

          args:
            command.args
        }
      })
    );

    console.log(
      (
        "⚡ PUSH "
        +
        command.action
        +
        " | "
        +
        command.id
      )
    );

    return "websocket";
  }

  if (
    commandQueue.length >=
    MAX_QUEUE
  ) {
    throw new Error(
      "Command queue is full"
    );
  }

  command.status =
    "queued";

  command.transport =
    "legacy-poll";

  commandQueue.push(
    command
  );

  commandResults.set(
    command.id,
    {
      id:
        command.id,

      action:
        command.action,

      status:
        "queued",

      createdAt:
        command.createdAt,

      transport:
        "legacy-poll",

      result:
        null
    }
  );

  console.log(
    (
      "📥 QUEUED "
      +
      command.action
      +
      " | "
      +
      command.id
    )
  );

  return "legacy-poll";
}


// ======================================================
// WAIT RESULT
// ======================================================

function waitForResult(
  commandId,
  timeoutMs =
    SYNC_COMMAND_TIMEOUT_MS
) {
  const existing =
    commandResults.get(
      commandId
    );

  if (
    existing?.status === "completed"
    ||
    existing?.status === "failed"
  ) {
    return Promise.resolve(
      existing
    );
  }

  return new Promise(
    (
      resolve,
      reject
    ) => {
      const timer =
        setTimeout(
          () => {
            resultWaiters.delete(
              commandId
            );

            reject(
              new Error(
                "Command timed out"
              )
            );
          },
          timeoutMs
        );

      resultWaiters.set(
        commandId,
        {
          resolve,
          reject,
          timer
        }
      );
    }
  );
}


// ======================================================
// HEALTH
// ======================================================

app.get(
  "/api/health",
  (
    req,
    res
  ) => {
    res.json({
      ok:
        true,

      service:
        "kemo-desktop",

      version:
        "2.1-whole-pc-realtime",

      deviceId:
        KEMO_DESKTOP_DEVICE_ID,

      securityConfigured:
        Boolean(
          KEMO_DESKTOP_KEY
        ),

      agentOnline:
        agentOnline(),

      realtimeWebSocket:
        websocketOnline(),

      transport:
        websocketOnline()
          ?
          "websocket"
          :
          "legacy",

      wholePcDirect:
        true,

      chromeDirect:
        true,

      windowsUIAutomation:
        true,

      foregroundControl:
        true,

      installedAppLauncher:
        true,

      lastAgentSeenAt,

      lastAgentInfo,

      queuedCommands:
        commandQueue.length,

      allowedActions:
        [...ALLOWED_ACTIONS],

      arbitraryShellExecution:
        false
    });
  }
);


// ======================================================
// ASYNC COMMAND
// ======================================================

app.post(
  "/api/command",
  requireDesktopKey,
  (
    req,
    res
  ) => {
    try {
      const action =
        cleanText(
          req.body?.action,
          100
        );

      const deviceId =
        cleanText(
          req.body?.deviceId
          ||
          KEMO_DESKTOP_DEVICE_ID,
          200
        );

      const command =
        createCommand(
          action,
          req.body?.args,
          deviceId
        );

      const transport =
        dispatchCommand(
          command
        );

      res.json({
        ok:
          true,

        commandId:
          command.id,

        status:
          command.status,

        transport
      });

    } catch (error) {
      res
        .status(400)
        .json({
          ok:
            false,

          error:
            error.message
        });
    }
  }
);


// ======================================================
// SYNC COMMAND
// ======================================================

app.post(
  "/api/command-sync",
  requireDesktopKey,
  async (
    req,
    res
  ) => {
    try {
      const action =
        cleanText(
          req.body?.action,
          100
        );

      const deviceId =
        cleanText(
          req.body?.deviceId
          ||
          KEMO_DESKTOP_DEVICE_ID,
          200
        );

      const timeoutMs =
        Math.max(
          1000,
          Math.min(
            60000,
            Number(
              req.body?.timeoutMs
              ||
              SYNC_COMMAND_TIMEOUT_MS
            )
          )
        );

      const command =
        createCommand(
          action,
          req.body?.args,
          deviceId
        );

      const transport =
        dispatchCommand(
          command
        );

      const finalResult =
        await waitForResult(
          command.id,
          timeoutMs
        );

      res.json({
        ok:
          finalResult.status
          ===
          "completed",

        commandId:
          command.id,

        transport,

        status:
          finalResult.status,

        result:
          finalResult.result
      });

    } catch (error) {
      res
        .status(
          error.message ===
          "Command timed out"
            ?
            504
            :
            400
        )
        .json({
          ok:
            false,

          error:
            error.message
        });
    }
  }
);


// ======================================================
// COMMAND STATUS
// ======================================================

app.get(
  "/api/command/:commandId",
  requireDesktopKey,
  (
    req,
    res
  ) => {
    const commandId =
      cleanText(
        req.params?.commandId,
        200
      );

    const result =
      commandResults.get(
        commandId
      );

    if (
      !result
    ) {
      return res
        .status(404)
        .json({
          ok:
            false,

          error:
            "Command not found"
        });
    }

    res.json({
      ok:
        true,

      command:
        result
    });
  }
);


// ======================================================
// LEGACY POLL
// ======================================================

app.get(
  "/api/agent/next",
  requireDesktopKey,
  (
    req,
    res
  ) => {
    const deviceId =
      cleanText(
        req.query?.deviceId,
        200
      );

    if (
      deviceId !==
      KEMO_DESKTOP_DEVICE_ID
    ) {
      return res
        .status(403)
        .json({
          ok:
            false,

          error:
            "Unknown device"
        });
    }

    lastAgentSeenAt =
      nowIso();

    const index =
      commandQueue.findIndex(
        command =>
          command.deviceId
          ===
          deviceId
      );

    if (
      index < 0
    ) {
      return res.json({
        ok:
          true,

        command:
          null
      });
    }

    const command =
      commandQueue.splice(
        index,
        1
      )[0];

    command.status =
      "running";

    command.startedAt =
      nowIso();

    commandResults.set(
      command.id,
      {
        id:
          command.id,

        action:
          command.action,

        status:
          "running",

        createdAt:
          command.createdAt,

        startedAt:
          command.startedAt,

        transport:
          "legacy-poll",

        result:
          null
      }
    );

    res.json({
      ok:
        true,

      command: {
        id:
          command.id,

        action:
          command.action,

        args:
          command.args
      }
    });
  }
);


// ======================================================
// LEGACY HEARTBEAT
// ======================================================

app.post(
  "/api/agent/heartbeat",
  requireDesktopKey,
  (
    req,
    res
  ) => {
    const deviceId =
      cleanText(
        req.body?.deviceId,
        200
      );

    if (
      deviceId !==
      KEMO_DESKTOP_DEVICE_ID
    ) {
      return res
        .status(403)
        .json({
          ok:
            false,

          error:
            "Unknown device"
        });
    }

    lastAgentSeenAt =
      nowIso();

    lastAgentInfo = {
      computer:
        cleanText(
          req.body?.computer,
          300
        ),

      windowsUser:
        cleanText(
          req.body?.windowsUser,
          300
        ),

      agentVersion:
        cleanText(
          req.body?.agentVersion,
          100
        ),

      transport:
        "legacy",

      capabilities:
        Array.isArray(
          req.body?.capabilities
        )
          ?
          req.body.capabilities
            .slice(
              0,
              200
            )
          :
          []
    };

    res.json({
      ok:
        true,

      serverTime:
        nowIso(),

      bridgeVersion:
        "2.1-whole-pc-realtime"
    });
  }
);


// ======================================================
// LEGACY RESULT
// ======================================================

app.post(
  "/api/agent/result",
  requireDesktopKey,
  (
    req,
    res
  ) => {
    const deviceId =
      cleanText(
        req.body?.deviceId,
        200
      );

    const commandId =
      cleanText(
        req.body?.commandId,
        200
      );

    if (
      deviceId !==
      KEMO_DESKTOP_DEVICE_ID
    ) {
      return res
        .status(403)
        .json({
          ok:
            false,

          error:
            "Unknown device"
        });
    }

    if (
      !commandResults.has(
        commandId
      )
    ) {
      return res
        .status(404)
        .json({
          ok:
            false,

          error:
            "Command not found"
        });
    }

    finalizeCommand(
      commandId,
      cleanText(
        req.body?.status,
        50
      ),
      req.body?.result
    );

    lastAgentSeenAt =
      nowIso();

    res.json({
      ok:
        true
    });
  }
);


// ======================================================
// WEBSOCKET UPGRADE
// ======================================================

server.on(
  "upgrade",
  (
    req,
    socket,
    head
  ) => {
    try {
      const parsed =
        new URL(
          req.url,
          "http://localhost"
        );

      if (
        parsed.pathname !==
        "/api/agent/ws"
      ) {
        socket.destroy();
        return;
      }

      const deviceId =
        cleanText(
          parsed.searchParams.get(
            "deviceId"
          ),
          200
        );

      const providedKey =
        cleanText(
          req.headers[
            "x-kemo-desktop-key"
          ],
          1000
        );

      if (
        deviceId !==
        KEMO_DESKTOP_DEVICE_ID
        ||
        !safeEqual(
          providedKey,
          KEMO_DESKTOP_KEY
        )
      ) {
        socket.write(
          "HTTP/1.1 401 Unauthorized\r\n"
          +
          "Connection: close\r\n"
          +
          "\r\n"
        );

        socket.destroy();
        return;
      }

      wss.handleUpgrade(
        req,
        socket,
        head,
        ws => {
          wss.emit(
            "connection",
            ws,
            req
          );
        }
      );

    } catch (error) {
      console.log(
        "⚠️ WebSocket upgrade:",
        error.message
      );

      socket.destroy();
    }
  }
);


// ======================================================
// WEBSOCKET CONNECTION
// ======================================================

wss.on(
  "connection",
  ws => {

    if (
      realtimeAgent
      &&
      realtimeAgent.readyState
      ===
      WebSocket.OPEN
    ) {
      try {
        realtimeAgent.close(
          4000,
          "Replaced by newer agent"
        );
      } catch {}
    }

    realtimeAgent =
      ws;

    lastAgentSeenAt =
      nowIso();

    console.log(
      "⚡ REALTIME Windows Agent CONNECTED"
    );

    ws.send(
      JSON.stringify({
        type:
          "connected",

        ok:
          true,

        bridgeVersion:
          "2.1-whole-pc-realtime",

        deviceId:
          KEMO_DESKTOP_DEVICE_ID,

        serverTime:
          nowIso()
      })
    );


    while (
      commandQueue.length > 0
      &&
      ws.readyState
      ===
      WebSocket.OPEN
    ) {
      const command =
        commandQueue.shift();

      dispatchCommand(
        command
      );
    }


    ws.on(
      "message",
      raw => {
        try {
          const message =
            JSON.parse(
              raw.toString()
            );

          const type =
            cleanText(
              message?.type,
              50
            );

          lastAgentSeenAt =
            nowIso();


          if (
            type ===
            "heartbeat"
          ) {
            lastAgentInfo = {
              computer:
                cleanText(
                  message?.computer,
                  300
                ),

              windowsUser:
                cleanText(
                  message?.windowsUser,
                  300
                ),

              agentVersion:
                cleanText(
                  message?.agentVersion,
                  100
                ),

              transport:
                "websocket",

              browserDirect:
                message?.browserDirect
                ===
                true,

              windowsUIA:
                message?.windowsUIA
                ===
                true,

              foregroundControl:
                message?.foregroundControl
                ===
                true,

              capabilities:
                Array.isArray(
                  message?.capabilities
                )
                  ?
                  message.capabilities
                    .slice(
                      0,
                      200
                    )
                  :
                  []
            };

            return;
          }


          if (
            type ===
            "result"
          ) {
            const commandId =
              cleanText(
                message?.commandId,
                200
              );

            if (
              !commandResults.has(
                commandId
              )
            ) {
              console.log(
                (
                  "⚠️ Unknown result: "
                  +
                  commandId
                )
              );

              return;
            }

            finalizeCommand(
              commandId,
              cleanText(
                message?.status,
                50
              ),
              message?.result
            );

            const final =
              commandResults.get(
                commandId
              );

            console.log(
              (
                final?.status ===
                "completed"
                  ?
                  "✅"
                  :
                  "❌"
              )
              +
              " RESULT "
              +
              final?.action
              +
              " | "
              +
              commandId
            );
          }

        } catch (error) {
          console.log(
            "⚠️ Bad WebSocket message:",
            error.message
          );
        }
      }
    );


    ws.on(
      "close",
      () => {
        if (
          realtimeAgent ===
          ws
        ) {
          realtimeAgent =
            null;
        }

        console.log(
          "⚠️ REALTIME Windows Agent disconnected"
        );
      }
    );


    ws.on(
      "error",
      error => {
        console.log(
          "⚠️ WebSocket error:",
          error.message
        );
      }
    );
  }
);


// ======================================================
// CLEANUP
// ======================================================

setInterval(
  () => {
    const now =
      Date.now();

    for (
      const [
        commandId,
        result
      ]
      of commandResults.entries()
    ) {
      const timestamp =
        result.completedAt
        ||
        result.startedAt
        ||
        result.createdAt;

      if (
        !timestamp
      ) {
        continue;
      }

      const age =
        now
        -
        new Date(
          timestamp
        ).getTime();

      if (
        age >
        RESULT_RETENTION_MS
      ) {
        commandResults.delete(
          commandId
        );

        commands.delete(
          commandId
        );
      }
    }
  },
  60000
).unref();


// ======================================================
// ROOT
// ======================================================

app.get(
  "/",
  (
    req,
    res
  ) => {
    res
      .type(
        "text/plain"
      )
      .send(
        "Kemo Desktop Bridge V2.1 Whole-PC Realtime is online."
      );
  }
);


// ======================================================
// START
// ======================================================

server.listen(
  PORT,
  "0.0.0.0",
  () => {
    console.log("");
    console.log(
      "======================================="
    );
    console.log(
      " KEMO DESKTOP BRIDGE V2.1"
    );
    console.log(
      " WHOLE-PC REALTIME"
    );
    console.log(
      "======================================="
    );
    console.log("");

    console.log(
      `✅ Port: ${PORT}`
    );

    console.log(
      `✅ Device: ${KEMO_DESKTOP_DEVICE_ID}`
    );

    console.log(
      (
        "🔐 Security key: "
        +
        (
          KEMO_DESKTOP_KEY
            ?
            "configured"
            :
            "MISSING"
        )
      )
    );

    console.log(
      "⚡ Persistent WebSocket ready"
    );

    console.log(
      "🌐 Chrome CDP commands allowed"
    );

    console.log(
      "🪟 Windows UI Automation commands allowed"
    );

    console.log(
      "🎯 Window foreground commands allowed"
    );

    console.log(
      "🚀 Installed app launching allowed"
    );

    console.log(
      "✅ /api/command-sync ready"
    );

    console.log(
      "🛡️ Explicit command allowlist"
    );

    console.log(
      "🚫 No arbitrary shell execution"
    );

    console.log("");
  }
);
