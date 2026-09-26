class Play extends Phaser.Scene
{
    constructor ()
    {
        super();
    }



    create ()
    {
  
        //add one extra pointer so two in total
        this.input.addPointer(1)
        this.moveLeft = false
        this.moveRight = false
        this.jump = false
        this.createWorld()
        this.jumpSound = this.sound.add('jump')
        this.coinSound = this.sound.add('coin')
        this.deadSound = this.sound.add('dead')
        

        this.scoreLabel = this.add.text(30,25,'Score: 0',{
            font:'18px Geo', 
            fill:'#fff',
            // fontWeight:
            // align:
            // backgroundColor:
        })
        this.score = 0
        this.player = this.physics.add.sprite(250,170,'player')
        
        this.player.body.gravity.y=500;
        this.coin = this.physics.add.sprite(60,150,'coin')
        this.enemies = this.physics.add.group()
        // this.time.addEvent({
        //     delay:2200,
        //     callback:()=>this.addEnemy(),
        //     loop:true,
        // }) 
        this.nextEnemy = 0
        this.space = this.input.keyboard.addKey("space")
         this.left = this.input.keyboard.addKey("left")
        this.right = this.input.keyboard.addKey("right")
        this.up = this.input.keyboard.addKey("up")
        this.physics.add.collider(this.player, this.walls);
        this.physics.add.collider(this.enemies, this.walls);

        this.anims.create({
            key:"right",
            frames:this.anims.generateFrameNumbers('player',{
                frames:[1,2]
            }),
            frameRate:8,
            repeat:-1,
        })
        this.anims.create({
            key:"left",
            frames:this.anims.generateFrameNumbers('player',{
                frames:[3,4]
            }),
            frameRate:8,
            repeat:-1,
        })
        
        const leftZone = this.add.zone(0, 170, this.sys.game.config.width / 2, this.sys.game.config.height)
            .setOrigin(0) // top-left corner
            .setInteractive(); // Make it respond to input

        const jumpZone = this.add.zone(0, 0, 500, 170)
            .setOrigin(0)
            .setInteractive();
        // Optional: visual debug shape
        // this.add.rectangle(0, 0, this.sys.game.config.width / 2, this.sys.game.config.height, 0xff0000, 0.2).setOrigin(0);

        const rightZone = this.add.zone(this.sys.game.config.width / 2, 170, this.sys.game.config.width, this.sys.game.config.height)
            .setOrigin(0) // top-left corner
            .setInteractive(); // Make it respond to input

        // Optional: visual debug shape
        // this.add.rectangle(this.sys.game.config.width / 2, 0, this.sys.game.config.width, this.sys.game.config.height, 0xff0000, 0.2).setOrigin(0);


leftZone.on('pointerdown',()=>{
    this.moveLeft = true;
})
leftZone.on('pointerup',()=>{
        this.moveLeft = false;
})
leftZone.on('pointerout', () => {
        this.moveLeft = false;
});

rightZone.on('pointerdown',()=>{
    this.moveRight = true;
})
    rightZone.on('pointerup',()=>{
            this.moveRight = false;
})
    rightZone.on('pointerout', () => {
            this.moveRight = false;
});

        jumpZone.on('pointerdown', () => {
            this.jump = true;

        });
                jumpZone.on('pointerup',()=>{
                     this.jump = false;
        })
            jumpZone.on('pointerout', () => {
                 this.jump = false;
        });

        this.rotateLabel = this.add.text(250,170,"",{
            font:'20px Geo',
            fill: '#fff',
            backgroundColor:'#000'
          })
                this.rotateLabel.setOrigin(0.5,0.5)

        
this.scale.on('orientationchange',this.orientationChange,this)
        this.orientationChange()




        
    }//end of create



    
    update(){
        // this.player.angle++;
        let now = Date.now()
        if (this.nextEnemy < now){
            let startDifficulty = 5000
            let endDifficulty = 500
            let scoreToReachEndDifficulty = 50
            let progress = Math.min(this.score/scoreToReachEndDifficulty,1)
            let delay = startDifficulty - (startDifficulty-endDifficulty)*progress
            this.addEnemy()
            this.nextEnemy = now + delay
        }
        this.movePlayer()

        if (this.physics.overlap(this.player,this.coin)){
            this.takeCoin()
        }

        if (this.physics.overlap(this.player,this.enemies)){
            this.playerDie()
        }
        
        if (this.player.y > 340 || this.player.y < 0){
            this.playerDie()
        }
    }//end of update
addEnemy(){
    let enemy = this.enemies.create(250,-10,'enemy')
    enemy.body.gravity.y = 500
    enemy.body.velocity.x = Phaser.Math.RND.pick([-100,100,30,-30])
    enemy.body.bounce.x = 1
    

    this.time.addEvent({
        delay:2000,
        callback: ()=>enemy.body.velocity.x = Phaser.Math.RND.pick([-100,100])
    })


    
    this.time.addEvent({
        delay:15000,
        callback: ()=>enemy.destroy()
    })
}
updateCoinPosition(){
    let positions = [
        {x:60,y:150},
         {x:420,y:150},
         {x:400,y:80},
         {x:100,y:80},
         {x:70,y:300},
         {x:450,y:300},
         {x:115,y:245},
         {x:380,y:245},
        
    ]

    let newPositions = [];

    for (let i = 0; i < positions.length; i++) {
        if (positions[i].x !== this.coin.x) {
            newPositions.push(positions[i]);
        }
    }

    positions = newPositions;

    let newPosition = Phaser.Math.RND.pick(positions)
    this.coin.setPosition(newPosition.x, newPosition.y)
    
}
    
    takeCoin(){
        this.score += 5
        this.coinSound.play()

        this.tweens.add({
            targets:this.player,
            scale:1.3,
            duration:100,
            yoyo:true,
        })

        
        this.scoreLabel.setText(`Score: ${this.score}`,{
                                   font:'18px Geo', 
                                   fill:'#fff',
                                   // fontWeight:
                                   // align:
                                   // backgroundColor:
                               })

        this.coin.setScale(0)
        this.tweens.add({
            targets:this.coin,
            scale:1,
            duration:300
        })

        
        this.updateCoinPosition()

       
    }
    
    createWorld(){
        const map = this.make.tilemap({ key: 'map' });
        //first parameter the name of the tileset in tiled
        //second parameter the name of the tileset in preload
        let tileset = map.addTilesetImage('tileset','tileset')
        this.walls = map.createLayer('Tile Layer 1', tileset)        
        this.walls.setCollision(1)
    }

    
movePlayer(){
    if(this.left.isDown){
        this.player.body.velocity.x = -200;
        this.player.anims.play('left',true)
    }
    else if(this.right.isDown){
        this.player.body.velocity.x = 200;
        this.player.anims.play('right',true)

    }
    else{
        this.player.body.velocity.x = 0;
        this.player.setFrame(0)
    }
    if (this.space.isDown && this.player.body.onFloor() || this.up.isDown && this.player.body.onFloor()) {
        this.jumpSound.play()
        this.player.body.velocity.y = -320;
    }

    if (this.moveRight){
        this.player.body.velocity.x = 200;
        this.player.anims.play('right',true)
    }
    if (this.moveLeft){
        this.player.body.velocity.x = -200;
        this.player.anims.play('left',true)
    }

    
    if (this.jump && this.player.body.onFloor()){
        this.player.body.velocity.y = -320;
        this.jumpSound.play()
    }

    
}

    playerDie(){
        this.deadSound.play()
        this.cameras.main.flash(300,255,50,35)
        this.cameras.main.shake(300,0.02)
        this.displayEmitter()

        this.time.addEvent({
            delay:1000,
            callback:()=> this.scene.start("menu",{score:this.score})
        })
        
    }

displayEmitter(){
    let particles = this.add.particles(this.player.x, this.player.y,'pixel',{
        number:100,
        angle: { min: 0, max: 360 },
        speed:{min:-150,max:150},
        lifespan:1000,
        duration:1000,

    })
}   


    orientationChange(){
        if(this.scale.orientation === Phaser.Scale.PORTRAIT){
            this.rotateLabel.setText("Rotate or exand your window to landscape")
            this.scene.pause()
        }
        else if(this.scale.orientation === Phaser.Scale.LANDSCAPE){
            this.rotateLabel.setText('')
            this.scene.resume()
        }
    }
}//end of scene


