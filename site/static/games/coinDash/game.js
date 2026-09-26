const config = {
    type: Phaser.AUTO,
    width: 500,
    height: 340,
    backgroundColor:'#3498db',
    physics: {
        default: 'arcade',
    },
    parent:'game',
    scale:{
        mode:Phaser.Scale.FIT,
        autoCenter:Phaser.Scale.CENTER_BOTH,
        min:{
            width:250,
            height:170,
        },
        max:{
            width:1000,
            height:680,
        },
    },
};

const game = new Phaser.Game(config);
game.scene.add('load',Load)
game.scene.add('menu',Menu);
game.scene.add('play',Play);

game.scene.start('load')
