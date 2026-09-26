class Menu extends Phaser.Scene{



create(data){
  // let score = data.score ? data.score:0
  let score
  let bestScore
  
  if (data.score){
   score = data.score
  }
  else{
    data.score = 0
    score = 0
  }

  bestScore = this.updateHighscore(score)

  this.add.image(250,170,'background')

  this.upKey = this.input.keyboard.addKey('up')

  let nameLabel = this.add.text(250,-50, 'Coin Collector',{
    font:'70px Geo',
    fill: '#fff'
  })
  nameLabel.setOrigin(0.5,0.5)


  this.tweens.add({
    targets:nameLabel,
    y:80,
    duration:1000,
    ease:'bounce.out'
  })

  let text;
  if (this.sys.game.device.os.desktop){
    text = 'Press Up to Start'
  }
  else{
    text = 'Touch Screen to Start'
  }
  
  let startText = this.add.text(250,170,text,{
    font:'35px Geo',
    fill: '#fff'
  })
startText.setOrigin(0.5,0.5)

this.tweens.add({
  targets:startText,
  angle:{from:-2,to:2},
  duration:1000,
  yoyo:true,
  repeat:-1
})

  
    let scoreText = this.add.text(250,250,'Score: '+ score +'\nBest Score: ' + bestScore,{
      font:'25px Geo',
      fill: '#fff'
    })
    scoreText.setOrigin(0.5,0.5)

  
}
  updateHighscore(newScore) {
    // get current highscore
    const oldHighscore = parseFloat(localStorage.getItem("coinCollector234"));
    if (
      oldHighscore !== oldHighscore || // if it doesn't exist yet
      oldHighscore < newScore
    ) {
      // or if it's smaller than the new score (I assume bigger means better here)
      // current highscore needs to be updated
      localStorage.setItem("coinCollector234", newScore);
      return newScore;
    }
    return oldHighscore;
  }

  update(){
  if (this.upKey.isDown || (!this.sys.game.device.os.desktop && this.input.activePointer.isDown)){
    this.scene.start('play')
  }


    
    // if (this.upKey.isDown){
    //   this.scene.start('play')
    // }
  }











  
}//end of menu scene
