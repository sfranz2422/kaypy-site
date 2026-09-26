class Load extends Phaser.Scene
{
preload ()
{
  // this.load.image('player','assets/player.png')
  this.load.spritesheet('player','assets/player2.png',{
    frameWidth: 20,
    frameHeight: 20,
  })
  this.load.image('background','assets/background.png')
  this.load.on('progress',this.progress,this)

  this.load.image('coin', 'assets/coin.png')
  this.load.on('progress',this.progress,this)

  this.load.image('enemy','assets/enemy.png')
  this.load.on('progress',this.progress,this)

  this.load.image('pixel','assets/pixel.png')
  this.load.on('progress',this.progress,this)

  this.load.image('tileset','tileset.png')
  this.load.on('progress',this.progress,this)

  this.load.tilemapTiledJSON('map','map.json')
  this.load.on('progress',this.progress,this)


  this.load.audio('jump',['assets/jump.ogg','assets/jump.mp3'])
  this.load.on('progress',this.progress,this)

  this.load.audio('coin',['assets/coin.ogg','assets/coin.mp3'])
  this.load.on('progress',this.progress,this)

  this.load.audio('dead',['assets/dead.ogg','assets/dead.mp3'])
  this.load.on('progress',this.progress,this)



// let loadLabel = this.add.text(250,170,'loading',{
//   font: '30px Arial',fill:'#fff'
// })
  this.loadLabel = this.add.text(250,170,'loading\n0%',{
    font:'35px Geo',fill:'#fff',align:'center'
  })
  this.loadLabel.setOrigin(0.5,0.5)

  
}//end of preload

progress(value){
  let percentage = Math.round(value*100)+ '%'
  this.loadLabel.setText('loading\n'+percentage)
}
  
create(){
  this.scene.start('menu')
}




}//end of scene