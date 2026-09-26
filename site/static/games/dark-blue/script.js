


kaplay({
    width: 600,
    height: 400,
    background: [0, 162, 255],
    letterbox: true,   // preserves 600:400 aspect ratio, adds bars if needed
    stretch: true,     // scales canvas CSS size to fill its container
});

// Gravity — you have setGravity(1200). 
// Lowering it (e.g. 900) makes jumps float higher and hang longer without touching jump speed at all — good if you want a floatier feel rather than just a higher snap.
// jumpFrames < 12 — t
// hat's how many frames the upward hold can be sustained 

// (your "hold jump for a bit more height" window). Raising it (e.g. 18) lets holding the key add more extra height on top of the base jump.
// gravityScale in player.onUpdate — currently 0.4 grounded / 1.0 airborne. Lowering the airborne value slightly (e.g. 0.85) also extends hang time at the top of the jump without changing takeoff speed.


setGravity(900);

loadSprite("player", "sprites/bean.png", { sliceX: 2, sliceY: 1 });
loadSprite("coin", "sprites/coin.png");
loadSprite("enemy", "sprites/ghosty.png");
loadSprite("tiles", "sprites/grass.png");

let soundEnabled = false;
let deadCount = 0;
const JUMPVELOCITY = 475

// --- LEVEL SELECT STATE ---
scene("LevelSelect", () => {
    add([
        text("choose a level (1-5)", { size: 25, font: "Arial" }),
        pos(width() / 2, height() / 2 - 40),
        anchor("center"),
    ]);

    add([
        text("press ESC to go back", { size: 16, font: "Arial" }),
        pos(width() / 2, height() / 2 + 60),
        anchor("center"),
    ]);

    for (let i = 1; i <= 5; i++) {
        add([
            text(`${i}`, { size: 30, font: "Arial" }),
            pos(width() / 2 + (i - 3) * 60, height() / 2),
            anchor("center"),
        ]);
        onKeyPress(`${i}`, () => go("Play", { levelId: i }));
    }

    onKeyPress("escape", () => go("Menu"));
});


// --- MENU STATE ---
scene("Menu", () => {
  
      add([
        text("Dark Blue Kaplay Version", { size: 40, font: "Arial" }),
        pos(width() / 2, height() / 2 - 80),
        anchor("center"),
    ]);
  
      add([
        text("Jump, collect coins, avoid the red stuff", { size: 18, font: "Arial" }),
        pos(width() / 2, height() / 2 - 30),
        anchor("center"),
    ]);
    const prompt = add([
        text("press UP to start, or DOWN to choose a level", { size: 22, font: "Arial" }),
        pos(width() / 2, height() - 50),
        anchor("center"),
        opacity(0),
    ]);

    add([
        text("based on \"Dark Blue\" by Thomas Palef (lessmilk.com)", { size: 12, font: "Arial" }),
        pos(width() / 2, height() - 15),
        anchor("center"),
        color(180, 180, 180),
    ]);
 deadCount = 0;

    wait(0.5, () => {
        tween(0, 1, 0.5, (v) => prompt.opacity = v);
        loop(1, () => {
            tween(1, -1, 0.5, (v) => prompt.angle = v)
             .onEnd(() => tween(-1, 1, 0.5, (v) => prompt.angle = v));
        });
    });

    onKeyPress("up", () => go("Play", { levelId: 1 }));
    onKeyPress("down", () => go("LevelSelect"));
});

// --- PLAY STATE ---
scene("Play", ({ levelId }) => {
    if (levelId === 1) deadCount = 0;
    let coinsTaken = 0;
onKeyPress("escape", () => go("Menu"));
    const levelData = maps[levelId];
    const { level, totalCoins } = buildLevelFromJSON(levelData);

    onUpdate("coin", (c) => {
        c.pos.y += Math.sin(time() * 5) * 0.5;
    });

    // Setup Player
const player = add([
    rect(20, 20), 
    color(255, 255, 255), 
    pos(spawnPos(levelId)),
    area(),
    body(),
    anchor("center"),
    rotate(0),
    "player"
]);


let _playerTransform = player.transform;
Object.defineProperty(player, "transform", {
    get() {
        return _playerTransform;
    },
    set(v) {
        // Only accept real Mat4-like objects (they have a working .clone())
        if (v && typeof v.clone === "function") {
            _playerTransform = v;
        }
        // otherwise: silently ignore the bad assignment, keep the last good transform
    },
    configurable: true
});


    player.onUpdate(() => {
          if (!(player.transform && typeof player.transform.clone === "function")) {
        console.log("BAD TRANSFORM", player.transform);
    }
        setCamPos(player.pos.x, player.pos.y); // Safe camera follow without vector references
        
        // Failsafe bounds check
        // if (player.pos.y < -30 || player.pos.y > height() + 100) playerDead();
                if (player.pos.y > height() + 100) playerDead();

        player.gravityScale = player.isGrounded() ? 0.4 : 1.0; 
    });

    // Player Movements
    onKeyDown("left", () => {
        player.move(player.isGrounded() ? -250 : -200, 0);
    });

    onKeyDown("right", () => {
        player.move(player.isGrounded() ? 250 : 200, 0);
    });

    let jumpFrames = 0;
    onKeyDown("up", () => {
        if (player.isGrounded()) {
            player.jump(JUMPVELOCITY);
            jumpFrames = 1;
        } else if (jumpFrames > 0 && jumpFrames < 12) {
            jumpFrames++;
            player.vel.y = (-1*JUMPVELOCITY);
        } else {
            jumpFrames = 0;
        }
    });
    onKeyRelease("up", () => jumpFrames = 0);

    // Collisions
  
  player.onCollide("ground", (tile) => {
    console.log("player.transform:", player.pos, player.transform, player.transform?.clone);
    console.log("tile.transform:", tile.pos, tile.transform, tile.transform?.clone);
    if (tile.isSpikeOrTrap) playerDead();
});
    player.onCollide("danger", () => playerDead());
    
    player.onCollide("coin", (c) => {
        coinsTaken++;
        tween(c.scale, vec2(0, 0), 0.2, (v) => c.scale = v).onEnd(() => c.destroy());
        if (coinsTaken === totalCoins) nextLevel();
    });

    player.onCollide("enemy", () => playerDead());
    
    player.onCollide("ground", (tile) => {
        if (tile.isSpikeOrTrap) playerDead(); 
    });

    // Enemy collision and movement routines
    onUpdate("enemy", (e) => {
        if (e.moveAxis === 1) e.move(e.moveDir * 100, 0);
        else if (e.moveAxis === 2) e.move(0, e.moveDir * 100);
    });

    onCollide("enemy", "ground", (e) => {
        e.moveDir *= -1;
    });

function playerDead() {
    deadCount++;
    player.pos = spawnPos(levelId);
    player.vel.y = 0;
    coinsTaken = 0;
}

  function spawnPos(levelId) {
    return vec2(
        levelId === 4 ? 100 : width() / 2 - 50,
        levelId === 5 ? height() / 2 - 100 : height() / 2
    );
}
    function nextLevel() {
        player.paused = true;
        tween(player.angle, 360, 0.6, (v) => player.angle = v).onEnd(() => {
            if (levelId === 5) { // Adjusted to 5 since maps only go up to map5
                go("Endd");
            } else {
                go("Play", { levelId: levelId + 1 });
            }
        });
    }
});

// --- END STATE ---
scene("Endd", () => {
    setCamPos(width() / 2, height() / 2); 

    // const logo = add([
    //     sprite("success"), // Will render silently as a blank space if not loaded
    //     pos(width() / 2, 150),
    //     anchor("center"),
    //     scale(0),
    // ]);
    tween(logo.scale, vec2(1, 1), 1, (v) => logo.scale = v, easings.easeOutBounce);

    const endText = add([
        text(`you died ${deadCount} times\n\npress the UP arrow key to restart`, { 
            size: 25, align: "center", font: "Arial" 
        }),
        pos(width() / 2, height() - 100),
        anchor("center"),
        opacity(0),
    ]);
    
    wait(0.5, () => {
        tween(0, 1, 0.5, (v) => endText.opacity = v);
        loop(1, () => {
            tween(1, -1, 0.5, (v) => endText.angle = v)
             .onEnd(() => tween(-1, 1, 0.5, (v) => endText.angle = v));
        });
    });

    wait(0.5, () => {
        onKeyPress("up", () => go("Menu"));
    });
});

function buildLevelFromJSON(levelData) {
    const width = levelData.width; 
    const height = levelData.height; 
    
    const tileLayer = levelData.layers.find(l => l.name === "layer").data;
    const objectLayer = levelData.layers.find(l => l.name === "objects").objects;

    const asciiMap = [];
    for (let y = 0; y < height; y++) {
        let row = [];
        for (let x = 0; x < width; x++) {
            const tileIndex = tileLayer[y * width + x];
            if (tileIndex === 1) row.push("="); 
            else if (tileIndex === 3) row.push("^"); 
            else row.push(" "); 
        }
        asciiMap.push(row);
    }

    const labels = [];
    let totalCoins = 0;

    for (const obj of objectLayer) {
        const gridX = Math.floor(obj.x / 20);
        const gridY = Math.floor(obj.y / 20) - 1; 

        if (obj.gid === 2) {
            asciiMap[gridY][gridX] = "$"; 
            totalCoins++;
        }
        else if (obj.gid === 4) asciiMap[gridY][gridX] = ">"; 
        else if (obj.gid === 5) asciiMap[gridY][gridX] = "v"; 
        else if (obj.gid === 7) {
            labels.push({ x: obj.x, y: obj.y - 20, text: obj.properties.text });
        }
    }

    const finalAsciiMap = asciiMap.map(row => row.join(""));

    const level = addLevel(finalAsciiMap, {
        tileWidth: 20,
        tileHeight: 20, 
        pos: vec2(0, 0),
        tiles: {
            "=": () => [
                rect(20, 20), 
              
                color(50, 200, 50), 
                area(), 
                body({ isStatic: true }), 
                "ground" // Replaced "layer"
            ],
            "^": () => [
                rect(20, 20), // Removed pos(0, 10) to prevent engine crash
                        // <- add this back
 
              color(200, 50, 50), 
                area(), 
                body({ isStatic: true }), 
                "danger"
            ], 
            "$": () => [
                circle(6), // Removed pos(10, 10) to prevent engine crash
                       
  
              color(255, 215, 0), 
                area({ isSensor: true }), 
                scale(1),
                "coin"
            ],
            ">": () => [
                rect(20, 20), 
                          
       
                color(255, 100, 100), 
                area(), 
              
                "enemy", // Removed body() to prevent gravity from crushing them
                { moveDir: 1, moveAxis: 1 }
            ],
            "v": () => [
                rect(20, 20), 
                         // <- add this back

                color(255, 100, 100), 
                area(), 
                "enemy", // Removed body() to prevent gravity from crushing them
                { moveDir: 1, moveAxis: 2 }
            ],
        }
    });

    for (const label of labels) {
        add([
            text(label.text, { size: 16, font: "Arial" }),
            pos(label.x, label.y),
            color(255, 255, 255)
        ]);
    }

    return { level, totalCoins };
}

go("Menu");