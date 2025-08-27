const { ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');

console.log('renderer.js loaded'); // スクリプトが読み込まれたことを確認

// JSONファイルのパス
const jsonFilePath = path.join(__dirname, 'ark_output.json');
console.log(jsonFilePath); // デバッグ用ログ

// ボタンのクリックイベント
document.querySelectorAll('.btn').forEach(button => {
  button.addEventListener('click', (event) => {
    console.log('Button clicked:', event.target.textContent); // デバッグ用ログ
    const selectedButtons = document.querySelectorAll('.btn-selected');

    // クリックされたボタンが既に選択されている場合は選択を解除
    if (event.target.classList.contains('btn-selected')) {
      event.target.classList.remove('btn-selected');
    } else {
      // 選択されているボタンが5個未満の場合のみ選択を追加
      if (selectedButtons.length < 5) {
        event.target.classList.add('btn-selected');
      }
    }

    // タグの組み合わせを分析
    analyzeTags();

    if (event.target.id === 'capture') {
      ipcRenderer.send('capture-screen');
    }
  });
});

// タグの組み合わせを分析する関数
function analyzeTags() {
  const selectedTags = Array.from(document.querySelectorAll('.btn-selected')).map(button => button.textContent.trim());
  console.log('Selected tags:', selectedTags); // デバッグ用ログ

  fs.readFile(jsonFilePath, 'utf-8', (err, data) => {
    if (err) {
      console.error('Error reading ark_output.json:', err);
      return;
    }

    const jsonData = JSON.parse(data);
    console.log('JSON data:', jsonData); // デバッグ用ログ
    const results = [];

    const filteredData = jsonData.filter(item => item.get.includes('公開求人'));

    if (selectedTags.length === 1 && selectedTags.includes('上級エリート')) {
      // 選択肢が一つだけかつ、上級エリートのみの場合
      filteredData.forEach(item => {
        if (item.retreat === '6') {
          const existingCombination = results.find(result => result.combination.join('＋') === selectedTags.join('＋'));
          if (existingCombination) {
            existingCombination.details.push({ name: item.name, img: item.img });
          } else {
            results.push({ combination: selectedTags, details: [{ name: item.name, img: item.img }] });
          }
        }
      });
    } else if (selectedTags.length === 1 && selectedTags.includes('エリート')) {
      // 選択肢が一つだけかつ、エリートのみの場合
      filteredData.forEach(item => {
        if (item.retreat === '5') {
          const existingCombination = results.find(result => result.combination.join('＋') === selectedTags.join('＋'));
          if (existingCombination) {
            existingCombination.details.push({ name: item.name, img: item.img });
          } else {
            results.push({ combination: selectedTags, details: [{ name: item.name, img: item.img }] });
          }
        }
      });
    } else if (selectedTags.length === 1) {
      // 選択肢が一つだけかつ、上級エリート かつエリートではない場合
      filteredData.forEach(item => {
        if (item.retreat !== '6' && selectedTags.every(tag => item.tag.includes(tag))) {
          const existingCombination = results.find(result => result.combination.join('＋') === selectedTags.join('＋'));
          if (existingCombination) {
            existingCombination.details.push({ name: item.name, img: item.img });
          } else {
            results.push({ combination: selectedTags, details: [{ name: item.name, img: item.img }] });
          }
        }
      });
    } else {
      // 複数のタグが選択されている場合
      const combinations = getCombinations(selectedTags);
      combinations.forEach(combination => {
        const matchedItems = filteredData.filter(item => {
          // 複数のタグが選択されている場合かつ上級エリートを選択しているとき
          if (selectedTags.includes('上級エリート') && !selectedTags.includes('エリート')) {
            return combination.every(tag => item.tag.includes(tag)) && item.retreat === '6';
          }
          // 複数のタグが選択されている場合かつエリートを選択しているとき
          if (selectedTags.includes('エリート') && !selectedTags.includes('上級エリート')) {
            return combination.every(tag => item.tag.includes(tag)) && item.retreat === '5';
          }
          // 複数のタグが選択されている場合かつ上級エリートとエリートどちらも選択されていないとき
          if (!selectedTags.includes('上級エリート') && !selectedTags.includes('エリート')) {
            return combination.every(tag => item.tag.includes(tag)) && item.retreat !== '6';
          }
          // 複数のタグが選択されている場合かつ上級エリートとエリートどちらも選択されているとき
          if (selectedTags.includes('上級エリート') && selectedTags.includes('エリート')) {
            return combination.every(tag => item.tag.includes(tag)) && item.retreat === '6';
          }
        }).map(item => ({ name: item.name, img: item.img }));

        if (matchedItems.length > 0) {
          const existingCombination = results.find(result => result.combination.join('＋') === combination.join('＋'));
          if (existingCombination) {
            existingCombination.details.push(...matchedItems);
          } else {
            results.push({ combination, details: matchedItems });
          }
        }
      });

      // 上級エリートとエリートどちらも選択されているとき、retreatが5と6の値をすべて表示
      if (selectedTags.includes('上級エリート') && selectedTags.includes('エリート')) {
        filteredData.forEach(item => {
          if (item.retreat === '5' || item.retreat === '6') {
            const existingCombination = results.find(result => result.combination.join('＋') === selectedTags.join('＋'));
            if (existingCombination) {
              existingCombination.details.push({ name: item.name, img: item.img });
            } else {
              results.push({ combination: selectedTags, details: [{ name: item.name, img: item.img }] });
            }
          }
        });
      }
    }

    //results.sort((a, b) => a.names.length - b.names.length);
    console.log('Results:', results); // デバッグ用ログ
    displayResults(results);
  });
}

// タグの組み合わせを取得する関数
function getCombinations(array) {
  const result = [];

  const f = (prefix, array) => {
    for (let i = 0; i < array.length; i++) {
      result.push([...prefix, array[i]]);
      f([...prefix, array[i]], array.slice(i + 1));
    }
  }

  f([], array);
  return result;
}

// 結果を表示する関数
function displayResults(results) {
  const resultContainer = document.getElementById('result-container');
  resultContainer.innerHTML = '';
  
  results.forEach((result,index) => {
    console.log('result.combination:', result.combination); // デバッグ用ログ
    //console.log('result.details:', result.details); // デバッグ用ログ

    const combinationContainer = document.createElement('div');
    combinationContainer.className = 'container mt-4';
    const combinationLabel = document.createElement('div');
    combinationLabel.className = 'border p-3 text-center';
    combinationLabel.textContent = `タグの組み合わせ: ${result.combination.join('＋')}`;
    combinationContainer.appendChild(combinationLabel);
    resultContainer.appendChild(combinationContainer);

    result.details.forEach((detail, detailIndex) => {
      //console.log('detail:', detail); // デバッグ用ログ
      //console.log('detail.name:', detail.name); // デバッグ用ログ

      const detailContainer = document.createElement('div');
      detailContainer.style.display = 'inline-block';
      detailContainer.style.textAlign = 'center';
      detailContainer.style.marginRight = '10px';

      const img = document.createElement('img');
      img.width = 100;
      img.height = 100;
      img.src = detail.img;
      img.alt = detail.name;

      // 画像が読み込めなかった場合の代替テキストを表示する処理
      img.onerror = function() {
        const altDiv = document.createElement('div');
        altDiv.textContent = detail.name;
        altDiv.style.width = '100px';
        altDiv.style.height = '100px';
        altDiv.style.display = 'flex';
        altDiv.style.alignItems = 'center';
        altDiv.style.justifyContent = 'center';
        altDiv.style.border = '1px solid #ccc';
        detailContainer.replaceChild(altDiv, img);
      };

      detailContainer.appendChild(img);

      const span = document.createElement('span');
      span.style.display = 'flex';
      span.textContent = detail.name;
      detailContainer.appendChild(span);

      resultContainer.appendChild(detailContainer);
  
      // Add a line break after every 8 labels
      //if ((detailIndex + 1) % 8 === 0) {
      //    resultContainer.appendChild(document.createElement('br'));
      //}
      //resultContainer.appendChild(document.createElement('br'));

    })


/*

    const namesLabel = document.createElement('div');
    const label = document.createElement('span');
    namesLabel.className = 'badge badge-secondary m-2';
    //namesLabel.textContent = result.names.join('　');
    label.textContent = result.names.join('　');
    namesLabel.appendChild(label);
    combinationContainer.appendChild(namesLabel);

*/
  });
}

// リセットボタンのクリックイベント
document.getElementById('reset').addEventListener('click', () => {
  // ElectronのViewをリロード
  window.location.reload();

  // リセット前にタグのクラスをクリア
/*
  document.querySelectorAll('.btn-selected').forEach(button => {
    button.classList.remove('btn-selected');
  });
*/
});

ipcRenderer.on('capture-success', (event, message) => {
  console.log('capture-success event received'); // デバッグ用ログ
  alert(message);
  // report.txtの内容を読み込んでボタンを選択状態にする
  const reportPath = path.join(__dirname, 'report.txt');
  fs.readFile(reportPath, 'utf-8', (err, data) => {
    if (err) {
      console.error('Error reading report.txt:', err);
      return;
    }
    console.log('report.txt content:', data); // デバッグ用ログ
    const lines = data.split('\n').map(line => line.trim());
    document.querySelectorAll('.btn').forEach(button => {
      console.log('Button text:', button.textContent.trim()); // デバッグ用ログ
      if (lines.includes(button.textContent.trim())) {
        console.log('Selecting button:', button.textContent.trim()); // デバッグ用ログ
        button.classList.add('btn-selected');
      }
    });
  });
});

ipcRenderer.on('capture-error', (event, message) => {
  alert(`Error: ${message}`);
});