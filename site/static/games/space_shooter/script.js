// =============================================================
//  SPACE SHOOTER  —  KAPLAY version
//  (converted from the original Phaser 3 project)
// =============================================================

kaplay({
    width: 400,
    height: 500,
    background: [52, 73, 94], // same #34495e as the Phaser version
    letterbox: true,
    crisp: true,
    font: "monospace",
});

// -------------------------------------------------------------
//  ASSETS  —  all from the standard KAPLAY Crew set
// -------------------------------------------------------------
// In the KAPLAY playground the crew sprites are served from /crew/.
// Running elsewhere? Use: const CREW = "https://play.kaplayjs.com/crew";
const CREW = "/crew";
loadSprite("apple", "sprites/apple.png");

loadSprite("player", `sprites/bean.png`);
loadSprite("enemy", `sprites/ghosty.png`);
loadSprite("bullet", `sprites/spike.png`);
loadSprite("bonus", `sprites/lightening.png`);

// -------------------------------------------------------------
//  TUNING CONSTANTS
// -------------------------------------------------------------
const WIDTH = 400;
const HEIGHT = 500;

const PLAYER_Y = 450;
const PLAYER_SPEED = 350;
const BULLET_SPEED = 400;
const FIRE_DELAY = 0.2; // seconds between shots

const START_LIVES = 3;
const ENEMY_HEALTH = 100;
const BULLET_DAMAGE = 25;

// Enemy spawn rate ramps up as the score climbs
const SPAWN_SLOW = 0.4; // seconds between enemies at score 0
const SPAWN_FAST = 0.1; // seconds between enemies at max difficulty
const SCORE_FOR_MAX_DIFFICULTY = 300;

const BONUS_EVERY = 15; // seconds

// -------------------------------------------------------------
//  LOADING SCREEN  (replaces the Phaser "load" scene)
// -------------------------------------------------------------
onLoading((progress) => {
    drawText({
        text: "loading",
        size: 30,
        pos: vec2(WIDTH / 2, HEIGHT / 2 - 20),
        anchor: "center",
    });
    drawText({
        text: `${Math.round(progress * 100)}%`,
        size: 30,
        pos: vec2(WIDTH / 2, HEIGHT / 2 + 20),
        anchor: "center",
    });
});

// -------------------------------------------------------------
//  SHARED HELPERS
// -------------------------------------------------------------

// White full-screen flash — stands in for Phaser's camera.flash()
function flashScreen() {
    const veil = add([
        rect(WIDTH, HEIGHT),
        pos(0, 0),
        color(255, 255, 255),
        opacity(0.7),
        fixed(),
        z(1000),
    ]);
    tween(0.7, 0, 0.15, (v) => (veil.opacity = v));
    wait(0.15, () => destroy(veil));
}

// Burst of pixels — stands in for Phaser's particle emitters
function explode(p, count, speed, life) {
    for (let i = 0; i < count; i++) {
        const angle = rand(0, Math.PI * 2);
        const dir = vec2(Math.cos(angle), Math.sin(angle));

        const piece = add([
            rect(4, 4),
            pos(p),
            anchor("center"),
            color(255, 255, 255),
            opacity(1),
            scale(2),
            move(dir, rand(speed * 0.3, speed)),
            z(50),
        ]);

        tween(1, 0, life, (v) => {
            piece.opacity = v;
            piece.scale = vec2(v * 2);
        });
        wait(life, () => destroy(piece));
    }
}

// One drifting background star
function spawnStar() {
    const star = add([
        rect(2, 2),
        pos(rand(0, WIDTH), 0),
        color(255, 255, 255),
        opacity(0.5),
        scale(rand(0.3, 0.8) * 3),
        move(DOWN, rand(100, 200)),
        z(-100),
    ]);
    star.onUpdate(() => {
        if (star.pos.y > HEIGHT + 10) destroy(star);
    });
}

// The scrolling starfield, used by both scenes
function addStarfield() {
    loop(0.1, spawnStar);
}

// =============================================================
//  MENU SCENE
// =============================================================
scene("menu", (data) => {
    const score = (data && data.score) || 0;

    addStarfield();

    // Game title, bouncing in
    const nameLabel = add([
        text("Space Shooter", { size: 36 }),
        pos(WIDTH / 2, 100),
        anchor("center"),
        scale(0),
    ]);
    wait(0.2, () => {
        tween(0, 1, 1, (v) => (nameLabel.scale = vec2(v)), easings.easeOutBounce);
    });

    // Last run's score, if there was one
    if (score > 0) {
        add([
            text(`score: ${score}`, { size: 24 }),
            pos(WIDTH / 2, 250),
            anchor("center"),
        ]);
    }

    // Blinking "how to start" prompt
    const startLabel = add([
        text("press the up arrow\nkey to start", { size: 22, align: "center" }),
        pos(WIDTH / 2, 400),
        anchor("center"),
        opacity(1),
    ]);
    startLabel.onUpdate(() => {
        // 1 -> 0 -> 1 over two seconds, same as the Phaser yoyo tween
        startLabel.opacity = (Math.cos(time() * Math.PI) + 1) / 2;
    });

    onKeyPress("up", () => go("play"));
});

// =============================================================
//  PLAY SCENE
// =============================================================
scene("play", () => {
    // --- state ---
    let lives = START_LIVES;
    let score = 0;
    let bonus = 1; // 1, 2 or 3 bullets per shot
    let nextBullet = 0;
    let nextEnemy = 0;
    let dead = false;

    addStarfield();

    // --- HUD ---
    const livesLabel = add([
        text(`lives: ${lives}`, { size: 18 }),
        pos(20, 20),
        fixed(),
        z(100),
    ]);

    const scoreLabel = add([
        text(`score: ${score}`, { size: 18 }),
        pos(WIDTH - 20, 20),
        anchor("topright"),
        fixed(),
        z(100),
    ]);

    // --- player ---
    const player = add([
        sprite("player", { width: 36, height: 36 }),
        pos(WIDTH / 2, PLAYER_Y),
        anchor("center"),
        area({ scale: 0.7 }),
        "player",
    ]);

    // -------------------------------------------------------------
    //  SPAWNING
    // -------------------------------------------------------------
    function fireBullet(x) {
        const bullet = add([
            sprite("bullet", { width: 12, height: 18 }),
            pos(x, player.pos.y - 20),
            anchor("bot"),
            area(),
            move(UP, BULLET_SPEED),
            "bullet",
        ]);
        bullet.onUpdate(() => {
            if (bullet.pos.y < -30) destroy(bullet);
        });
    }

    function playerFire() {
        // Little recoil nudge
        player.pos.y = PLAYER_Y + 5;
        wait(0.05, () => {
            if (player.exists()) player.pos.y = PLAYER_Y;
        });

        // More bonuses collected = more bullets per shot
        if (bonus === 1) {
            fireBullet(player.pos.x);
        } else if (bonus === 2) {
            fireBullet(player.pos.x - 10);
            fireBullet(player.pos.x + 10);
        } else {
            fireBullet(player.pos.x - 15);
            fireBullet(player.pos.x);
            fireBullet(player.pos.x + 15);
        }
    }

function newEnemy() {
        const randomNumber = Math.floor(Math.random() * 4); // 0 to 3
        
        let eColor = rgb(255, 255, 255);
        let eSpeed = rand(100, 200);

        const zigWidth = 300; // How wide the left/right movement is
        const zigSpeed = 5; // How fast it switches directions
        let eHealth = 100; // 4 hits (Slowest)

        if (randomNumber === 1){
            eColor = rgb(0, 255, 0);
            eSpeed = rand(200, 300);
            eHealth = 75; // 3 hits
        } else if (randomNumber === 2){
            eColor = rgb(0, 0, 255);
            eSpeed = rand(300, 400);
            eHealth = 50; // 2 hits
        } else if (randomNumber === 3){
            eColor = rgb(255, 0, 0);
            eSpeed = rand(400, 500);
            eHealth = 25; // 1 hit (Fastest)
        }

        let enemy = add([
            sprite("enemy", { width: 34, height: 34 }),
            pos(rand(40, WIDTH - 40), 0),
            anchor("bot"),
            area({ scale: 0.8 }),
            color(eColor),
            scale(1),
            health(eHealth),
           
            "enemy",
            { origColor: eColor } // Save the color to fix the hit flash
        ]);

        const offset = rand(0, 10);
        enemy.onUpdate(() => {
            const s = Math.sin((time() + offset) * 8) * 0.08;
            enemy.move(Math.sin(time() * zigSpeed) * zigWidth, eSpeed);
            enemy.scale = vec2(1 + s, 1 - s);
            if (enemy.pos.y > HEIGHT + 40) destroy(enemy);
        });

        enemy.on("death", () => {
            explode(enemy.pos, 20, 150, 0.5);
            destroy(enemy);
            increaseScore(5);
        });
    }

    function newBonus() {
        const b = add([
            sprite("bonus", { width: 26, height: 26 }),
            pos(rand(20, WIDTH - 20), 0),
            anchor("center"),
            area(),
            rotate(0),
            move(DOWN, 150),
            "bonus",
        ]);
        b.onUpdate(() => {
            b.angle += 100 * dt(); // same spin as the Phaser angularVelocity
            if (b.pos.y > HEIGHT + 40) destroy(b);
        });
    }

    loop(BONUS_EVERY, newBonus);

    // -------------------------------------------------------------
    //  SCORING
    // -------------------------------------------------------------
    function increaseScore(amount) {
        score += amount;
        scoreLabel.text = `score: ${score}`;
    }

    // -------------------------------------------------------------
    //  COLLISIONS
    // -------------------------------------------------------------
onCollide("bullet", "enemy", (bullet, enemy) => {
        destroy(bullet);

        enemy.pos.y -= 10;
        
        // Flash bright white, then return to the correct color tier
        enemy.color = rgb(255, 255, 255);
        wait(0.1, () => {
            if (enemy.exists()) enemy.color = enemy.origColor;
        });

        enemy.hurt(BULLET_DAMAGE); 
    });

    onCollide("player", "bonus", (p, b) => {
        destroy(b);
        bonus += 1;
        increaseScore(25);

        // Quick pop on the player
        player.scale = vec2(1.4);
        wait(0.1, () => {
            if (player.exists()) player.scale = vec2(1);
        });
    });

    onCollide("player", "enemy", (p, enemy) => {
        if (dead) return;

        destroy(enemy);
        flashScreen();
        shake(8);

        bonus = 1; // lose the firepower upgrade
        lives -= 1;
        livesLabel.text = `lives: ${lives}`;

        if (lives <= 0) {
            dead = true;
            explode(player.pos, 15, 150, 1);
            destroy(player);
            wait(1.5, () => go("menu", { score: score }));
        }
    });

    // -------------------------------------------------------------
    //  MAIN LOOP
    // -------------------------------------------------------------
    onUpdate(() => {
        // Ramp the enemy spawn rate up with the score
        const progress = Math.min(score / SCORE_FOR_MAX_DIFFICULTY, 1);
        const delay = SPAWN_SLOW - (SPAWN_SLOW - SPAWN_FAST) * progress;

        if (time() > nextEnemy) {
            newEnemy();
            nextEnemy = time() + delay;
        }

        if (dead) return;

        // Move
        if (isKeyDown("left")) player.move(-PLAYER_SPEED, 0);
        else if (isKeyDown("right")) player.move(PLAYER_SPEED, 0);
        player.pos.x = clamp(player.pos.x, 18, WIDTH - 18);

        // Shoot
        if (isKeyDown("up") && time() > nextBullet) {
            nextBullet = time() + FIRE_DELAY;
            playerFire();
        }
    });
});

// =============================================================
go("menu");