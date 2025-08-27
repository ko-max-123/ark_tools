const { ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');

console.log('renderer.js loaded');

// JSONファイルのパス
const jsonFilePath = path.join(__dirname, 'ark_output.json');
console.log(jsonFilePath);

// 選択されたタグの数を制限
const MAX_SELECTED_TAGS = 5;

// パフォーマンス最適化のための変数
let selectedTagsCache = new Set();
let resultsCache = new Map();
let isAnalyzing = false;

// 選択カウンター要素
let selectionCounter = null;

// 初期化
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing...');
  
  // 初期状態でローディングを非表示
  showLoading(false);
  
  // 選択カウンターの作成
  createSelectionCounter();
  
  // タグボタンにイベントリスナーを追加
  initializeTagButtons();
  
  // キーボードショートカットの設定
  setupKeyboardShortcuts();
  
  // アクセシビリティの向上
  enhanceAccessibility();
  
  // パフォーマンス監視
  setupPerformanceMonitoring();
});

// 選択カウンターの作成
function createSelectionCounter() {
  selectionCounter = document.createElement('div');
  selectionCounter.className = 'selection-counter';
  selectionCounter.style.display = 'none';
  document.body.appendChild(selectionCounter);
  updateSelectionCounter();
}

// 選択カウンターの更新
function updateSelectionCounter() {
  const selectedCount = document.querySelectorAll('.tag-button.btn-selected').length;
  if (selectedCount > 0) {
    selectionCounter.style.display = 'block';
    selectionCounter.innerHTML = `
      <i class="fas fa-tags me-2"></i>
      選択中: ${selectedCount}/${MAX_SELECTED_TAGS}
    `;
  } else {
    selectionCounter.style.display = 'none';
  }
}

// タグボタンの初期化
function initializeTagButtons() {
  document.querySelectorAll('.tag-button').forEach(button => {
    button.addEventListener('click', handleTagButtonClick);
    
    // ホバーエフェクトの追加
    button.addEventListener('mouseenter', () => {
      if (!button.classList.contains('btn-selected')) {
        button.style.transform = 'translateY(-2px)';
      }
    });
    
    button.addEventListener('mouseleave', () => {
      if (!button.classList.contains('btn-selected')) {
        button.style.transform = 'translateY(0)';
      }
    });
    
    // アクセシビリティの向上
    button.setAttribute('role', 'button');
    button.setAttribute('tabindex', '0');
    button.setAttribute('aria-pressed', 'false');
  });
}

// タグボタンのクリック処理
function handleTagButtonClick(event) {
  const button = event.target;
  console.log('Button clicked:', button.textContent);
  
  // クリックされたボタンが既に選択されている場合は選択を解除
  if (button.classList.contains('btn-selected')) {
    button.classList.remove('btn-selected');
    button.classList.add('fade-in');
    button.setAttribute('aria-pressed', 'false');
    
    // 選択解除のアニメーション
    button.style.animation = 'fadeOut 0.3s ease-out';
    setTimeout(() => {
      button.style.animation = '';
    }, 300);
  } else {
    // 選択されているボタンが最大数未満の場合のみ選択を追加
    const selectedButtons = document.querySelectorAll('.tag-button.btn-selected');
    if (selectedButtons.length < MAX_SELECTED_TAGS) {
      button.classList.add('btn-selected');
      button.classList.add('fade-in');
      button.setAttribute('aria-pressed', 'true');
      
      // 選択成功のアニメーション
      button.classList.add('pulse');
      setTimeout(() => {
        button.classList.remove('pulse');
      }, 1000);
      
      // 触覚フィードバック（モバイル対応）
      if ('vibrate' in navigator) {
        navigator.vibrate(50);
      }
    } else {
      // 最大数に達した場合のフィードバック
      showNotification('最大5個までタグを選択できます', 'warning');
      
      // 視覚的フィードバック
      button.style.animation = 'shake 0.5s ease-in-out';
      setTimeout(() => {
        button.style.animation = '';
      }, 500);
      return;
    }
  }
  
  // 選択カウンターの更新
  updateSelectionCounter();
  
  // タグの組み合わせを分析（デバウンス処理）
  debounceAnalyzeTags();
}

// デバウンス処理によるタグ分析の最適化
let analyzeTimeout;
function debounceAnalyzeTags() {
  clearTimeout(analyzeTimeout);
  analyzeTimeout = setTimeout(() => {
    analyzeTags();
  }, 300);
}

// 通知を表示する関数
function showNotification(message, type = 'info') {
  // 既存の通知を削除
  const existingNotification = document.querySelector('.notification');
  if (existingNotification) {
    existingNotification.remove();
  }

  const notification = document.createElement('div');
  notification.className = `notification alert alert-${type === 'warning' ? 'warning' : 'info'} alert-dismissible fade show position-fixed`;
  notification.style.cssText = `
    top: 20px;
    right: 20px;
    z-index: 9999;
    min-width: 300px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border: none;
    border-radius: 8px;
  `;
  
  notification.innerHTML = `
    <i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="閉じる"></button>
  `;
  
  document.body.appendChild(notification);
  
  // 3秒後に自動で消す
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove();
    }
  }, 3000);
}

// タグの組み合わせを分析する関数
async function analyzeTags() {
  if (isAnalyzing) return;
  
  const selectedTags = Array.from(document.querySelectorAll('.tag-button.btn-selected')).map(button => button.textContent.trim());
  console.log('Selected tags:', selectedTags);
  
  // キャッシュチェック
  const cacheKey = selectedTags.sort().join('|');
  if (resultsCache.has(cacheKey)) {
    console.log('Using cached results');
    displayResults(resultsCache.get(cacheKey));
    return;
  }

  // ローディング表示
  showLoading(true);
  isAnalyzing = true;

  try {
    const data = await fs.promises.readFile(jsonFilePath, 'utf-8');
    const jsonData = JSON.parse(data);
    console.log('JSON data loaded');
    
    const results = await processData(jsonData, selectedTags);
    
    // キャッシュに保存
    resultsCache.set(cacheKey, results);
    
    // キャッシュサイズの制限（メモリ使用量の制御）
    if (resultsCache.size > 100) {
      const firstKey = resultsCache.keys().next().value;
      resultsCache.delete(firstKey);
    }
    
    displayResults(results);
    
    if (results.length > 0) {
      showNotification(`${results.length}件の組み合わせが見つかりました`, 'info');
    } else {
      showNotification('条件に一致するオペレーターが見つかりませんでした', 'warning');
    }
    
  } catch (error) {
    console.error('Error analyzing tags:', error);
    showNotification('データの解析に失敗しました', 'warning');
  } finally {
    showLoading(false);
    isAnalyzing = false;
  }
}

// 画像パスを絶対パスに変換する関数
function convertImagePathToAbsolute(imagePath) {
  // 既に絶対パスの場合はそのまま返す
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://') || imagePath.startsWith('file://')) {
    return imagePath;
  }
  
  // ビルドされたアプリでの正しいパスを取得
  let basePath;
  if (process.env.NODE_ENV === 'production' || process.resourcesPath) {
    // ビルドされたアプリの場合
    basePath = require('path').join(process.resourcesPath, 'app.asar.unpacked');
  } else {
    // 開発モードの場合
    basePath = __dirname;
  }
  
  // 画像パスを結合
  const absolutePath = require('path').join(basePath, imagePath);
  console.log(`画像パス変換: "${imagePath}" -> "${absolutePath}"`);
  
  // ファイルの存在確認
  if (require('fs').existsSync(absolutePath)) {
    console.log(`画像ファイル存在確認: OK - ${absolutePath}`);
  } else {
    console.warn(`画像ファイル存在確認: NG - ${absolutePath}`);
    
    // 代替パスを試す
    const alternativePaths = [
      require('path').join(__dirname, imagePath),
      require('path').join(process.cwd(), imagePath),
      require('path').join(process.resourcesPath || '', imagePath),
      require('path').join(process.resourcesPath || '', 'app.asar.unpacked', imagePath)
    ];
    
    for (const altPath of alternativePaths) {
      if (require('fs').existsSync(altPath)) {
        console.log(`代替パスで画像ファイル発見: ${altPath}`);
        return altPath;
      }
    }
  }
  
  return absolutePath;
}

// データ処理の分離（パフォーマンス向上）
async function processData(jsonData, selectedTags) {
  const results = [];
  
  // 公開求人のみを対象にフィルタリング
  const filteredData = jsonData.filter(item => item.get.includes('公開求人'));
  
  // 画像パスを絶対パスに変換
  filteredData.forEach(item => {
    if (item.img) {
      item.img = convertImagePathToAbsolute(item.img);
    }
  });
  
  // Web Workerを使用して重い処理を非同期で実行
  if (selectedTags.length > 0) {
    const combinations = generateCombinations(selectedTags);
    
    for (const size of [3, 2, 1]) {
      if (selectedTags.length >= size) {
        const sizeCombinations = combinations.filter(combo => combo.length === size);
        await analyzeCombinations(sizeCombinations, filteredData, results, selectedTags);
      }
    }
  }
  
  return results;
}

// 組み合わせ生成の最適化
function generateCombinations(array) {
  const result = [];
  
  function combine(prefix, arr, size) {
    if (prefix.length === size) {
      result.push([...prefix]);
      return;
    }
    
    for (let i = 0; i < arr.length; i++) {
      combine([...prefix, arr[i]], arr.slice(i + 1), size);
    }
  }
  
  for (let size = 1; size <= Math.min(array.length, 3); size++) {
    combine([], array, size);
  }
  
  return result;
}

// 組み合わせ分析の最適化
async function analyzeCombinations(combinations, filteredData, results, selectedTags) {
  for (const combination of combinations) {
    const matchedItems = filteredData.filter(item => {
      // retreatが6の場合、上級エリートタグが選択されていない場合は対象外
      if (item.retreat === '6' && !selectedTags.includes('上級エリート')) {
        return false;
      }
      return combination.every(tag => item.tag.includes(tag));
    }).map(item => ({ name: item.name, img: item.img }));

    if (matchedItems.length > 0) {
      const existingCombination = results.find(result => 
        result.combination.join('＋') === combination.join('＋')
      );
      
      if (existingCombination) {
        existingCombination.details.push(...matchedItems);
      } else {
        results.push({ combination, details: matchedItems });
      }
    }
    
    // 非同期処理によるUIのブロッキング防止
    if (combinations.indexOf(combination) % 10 === 0) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
}

// ローディング表示/非表示の制御
function showLoading(show) {
  const loadingElement = document.getElementById('loading');
  if (loadingElement) {
    loadingElement.style.display = show ? 'block' : 'none';
  }
}

// 結果を表示する関数
function displayResults(results) {
  const resultContainer = document.getElementById('result-container');
  resultContainer.innerHTML = '';
  
  if (results.length === 0) {
    resultContainer.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-search"></i>
        <h5>結果が見つかりません</h5>
        <p>選択されたタグの組み合わせに一致するオペレーターがいません</p>
      </div>
    `;
    return;
  }
  
  results.forEach((result, index) => {
    console.log('result.combination:', result.combination);

    const resultSection = document.createElement('div');
    resultSection.className = 'result-section fade-in';
    resultSection.style.animationDelay = `${index * 0.1}s`;

    const resultHeader = document.createElement('div');
    resultHeader.className = 'result-header';
    resultHeader.innerHTML = `
      <i class="fas fa-tags"></i>
      タグの組み合わせ: ${result.combination.join('＋')}
      <span class="badge bg-light text-dark ms-2">${result.details.length}件</span>
    `;
    
    const resultContent = document.createElement('div');
    resultContent.className = 'result-content';

    result.details.forEach((detail, detailIndex) => {
      const operatorCard = document.createElement('div');
      operatorCard.className = 'operator-card fade-in';
      operatorCard.style.animationDelay = `${(index * 0.1) + (detailIndex * 0.05)}s`;
      operatorCard.setAttribute('role', 'button');
      operatorCard.setAttribute('tabindex', '0');
      operatorCard.setAttribute('aria-label', `${detail.name}の詳細を表示`);

      const img = document.createElement('img');
      img.className = 'operator-image';
      img.src = detail.img;
      img.alt = detail.name;
      img.loading = 'lazy'; // 遅延読み込み

      // 画像が読み込めなかった場合の代替表示
      img.onerror = function() {
        console.error(`画像読み込みエラー: ${detail.name} - ${detail.img}`);
        console.error(`現在のディレクトリ: ${__dirname}`);
        console.error(`リソースパス: ${process.resourcesPath}`);
        console.error(`画像の絶対パス: ${detail.img}`);
        
        // ファイルの存在確認
        try {
          if (require('fs').existsSync(detail.img)) {
            console.error(`ファイル存在確認: OK`);
          } else {
            console.error(`ファイル存在確認: NG`);
            
            // 代替パスでの存在確認
            const alternativePaths = [
              require('path').join(__dirname, 'img', require('path').basename(detail.img)),
              require('path').join(process.cwd(), 'img', require('path').basename(detail.img)),
              require('path').join(process.resourcesPath || '', 'img', require('path').basename(detail.img)),
              require('path').join(process.resourcesPath || '', 'app.asar.unpacked', 'img', require('path').basename(detail.img))
            ];
            
            console.error('代替パスでの確認:');
            alternativePaths.forEach((altPath, index) => {
              const exists = require('fs').existsSync(altPath);
              console.error(`  ${index + 1}. ${altPath}: ${exists ? 'OK' : 'NG'}`);
            });
          }
        } catch (err) {
          console.error(`ファイル存在確認エラー: ${err.message}`);
        }
        
        const altDiv = document.createElement('div');
        altDiv.className = 'operator-image d-flex align-items-center justify-content-center bg-light text-muted';
        altDiv.innerHTML = `<i class="fas fa-user fa-2x"></i>`;
        operatorCard.replaceChild(altDiv, img);
      };
      
      // 画像読み込み成功時のログ
      img.onload = function() {
        console.log(`画像読み込み成功: ${detail.name} - ${detail.img}`);
      };

      const operatorName = document.createElement('p');
      operatorCard.className = 'operator-name';
      operatorName.textContent = detail.name;

      operatorCard.appendChild(img);
      operatorCard.appendChild(operatorName);
      resultContent.appendChild(operatorCard);
    });

    resultSection.appendChild(resultHeader);
    resultSection.appendChild(resultContent);
    resultContainer.appendChild(resultSection);
  });
}

// リセットボタンのクリックイベント
document.getElementById('reset').addEventListener('click', () => {
  // 確認ダイアログ
  if (confirm('すべての選択をリセットしますか？')) {
    // 選択されたタグのクラスをクリア
    document.querySelectorAll('.tag-button.btn-selected').forEach(button => {
      button.classList.remove('btn-selected');
      button.setAttribute('aria-pressed', 'false');
    });
    
    // 結果をクリア
    document.getElementById('result-container').innerHTML = '';
    
    // キャッシュをクリア
    resultsCache.clear();
    
    // 選択カウンターを更新
    updateSelectionCounter();
    
    // リセット成功の通知
    showNotification('選択がリセットされました', 'info');
  }
});

// キャプチャボタンのクリックイベント
document.getElementById('capture').addEventListener('click', () => {
  showNotification('画面キャプチャを開始しています...', 'info');
  ipcRenderer.send('capture-screen');
});

// IPC通信のイベントハンドラー
ipcRenderer.on('capture-success', (event, message, reportPathFromMain) => {
  console.log('capture-success event received');
  showNotification(message, 'info');
  
  // メインプロセスから送信されたパスを使用、またはフォールバック
  let reportPath = reportPathFromMain;
  
  if (!reportPath) {
    // ビルドされたアプリでの正しいパスを取得
    // 環境変数とプロセス情報からビルド状態を判定
    const isPackaged = process.env.NODE_ENV === 'production' || 
                       process.env.ELECTRON_IS_DEV === 'false' ||
                       process.resourcesPath !== undefined;
    
    if (isPackaged && process.resourcesPath) {
      // ビルドされたアプリの場合
      reportPath = require('path').join(process.resourcesPath, 'app.asar.unpacked', 'report.txt');
    } else {
      // 開発モードの場合
      reportPath = require('path').join(__dirname, 'report.txt');
    }
  }
  
  console.log('Report file path:', reportPath);
  console.log('Is packaged:', process.env.NODE_ENV === 'production');
  console.log('Resources path:', process.resourcesPath);
  
  // ファイルの存在確認
  if (!require('fs').existsSync(reportPath)) {
    console.error('Report file not found:', reportPath);
    
    // 代替パスを試す
    const alternativePaths = [
      require('path').join(__dirname, 'report.txt'),
      require('path').join(process.cwd(), 'report.txt'),
      require('path').join(process.resourcesPath || '', 'report.txt')
    ];
    
    console.log('Trying alternative paths:', alternativePaths);
    
    for (const altPath of alternativePaths) {
      if (require('fs').existsSync(altPath)) {
        console.log('Found report file at alternative path:', altPath);
        reportPath = altPath;
        break;
      }
    }
    
    if (!require('fs').existsSync(reportPath)) {
      showNotification('レポートファイルが見つかりません', 'warning');
      return;
    }
  }
  
  fs.readFile(reportPath, 'utf-8', (err, data) => {
    if (err) {
      console.error('Error reading report.txt:', err);
      showNotification('レポートファイルの読み込みに失敗しました', 'warning');
      return;
    }
    
    console.log('report.txt content:', data);
    const lines = data.split('\n').map(line => line.trim()).filter(line => line);
    console.log('Parsed lines:', lines);
    
    // 既存の選択をクリア
    document.querySelectorAll('.tag-button.btn-selected').forEach(button => {
      button.classList.remove('btn-selected');
      button.setAttribute('aria-pressed', 'false');
    });
    
    // レポートの内容に基づいてボタンを選択
    let selectedCount = 0;
    document.querySelectorAll('.tag-button').forEach(button => {
      const buttonText = button.textContent.trim();
      console.log(`Checking button: "${buttonText}"`);
      
      // より柔軟な照合（部分一致も含む）
      const isMatch = lines.some(line => {
        const match = line.includes(buttonText) || buttonText.includes(line);
        console.log(`  Comparing "${line}" with "${buttonText}": ${match}`);
        return match;
      });
      
      if (isMatch && selectedCount < MAX_SELECTED_TAGS) {
        console.log('Selecting button:', buttonText);
        button.classList.add('btn-selected');
        button.setAttribute('aria-pressed', 'true');
        selectedCount++;
      }
    });
    
    // 選択カウンターを更新
    updateSelectionCounter();
    
    // 選択されたタグで検索を実行
    analyzeTags();
    
    showNotification(`${selectedCount}個のタグが自動選択されました`, 'info');
  });
});

ipcRenderer.on('capture-error', (event, message) => {
  showNotification(`キャプチャエラー: ${message}`, 'warning');
});

// キーボードショートカットの設定
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (event) => {
    // Ctrl+R でリセット
    if (event.ctrlKey && event.key === 'r') {
      event.preventDefault();
      document.getElementById('reset').click();
    }
    
    // Ctrl+C でキャプチャ
    if (event.ctrlKey && event.key === 'c') {
      event.preventDefault();
      document.getElementById('capture').click();
    }
    
    // Escape で選択解除
    if (event.key === 'Escape') {
      document.querySelectorAll('.tag-button.btn-selected').forEach(button => {
        button.classList.remove('btn-selected');
        button.setAttribute('aria-pressed', 'false');
      });
      updateSelectionCounter();
      analyzeTags();
    }
    
    // 数字キーでタグ選択（1-9）
    if (event.key >= '1' && event.key <= '9') {
      const tagButtons = document.querySelectorAll('.tag-button');
      const index = parseInt(event.key) - 1;
      if (tagButtons[index]) {
        tagButtons[index].click();
      }
    }
  });
}

// アクセシビリティの向上
function enhanceAccessibility() {
  // フォーカス管理
  document.addEventListener('focusin', (event) => {
    if (event.target.classList.contains('tag-button') || 
        event.target.classList.contains('operator-card')) {
      event.target.style.outline = '2px solid var(--primary-color)';
      event.target.style.outlineOffset = '2px';
    }
  });
  
  document.addEventListener('focusout', (event) => {
    if (event.target.classList.contains('tag-button') || 
        event.target.classList.contains('operator-card')) {
      event.target.style.outline = '';
      event.target.style.outlineOffset = '';
    }
  });
  
  // スクリーンリーダー対応
  document.querySelectorAll('.tag-button').forEach(button => {
    button.setAttribute('aria-describedby', 'tag-description');
  });
  
  // 説明テキストの追加
  const description = document.createElement('div');
  description.id = 'tag-description';
  description.className = 'sr-only';
  description.textContent = 'タグを選択してオペレーターを検索できます。最大5個まで選択可能です。';
  document.body.appendChild(description);
}

// パフォーマンス監視の設定
function setupPerformanceMonitoring() {
  // メモリ使用量の監視
  if ('memory' in performance) {
    setInterval(() => {
      const memory = performance.memory;
      if (memory.usedJSHeapSize > 100 * 1024 * 1024) { // 100MB以上
        console.warn('High memory usage detected:', memory.usedJSHeapSize / 1024 / 1024, 'MB');
        // キャッシュのクリア
        resultsCache.clear();
      }
    }, 30000); // 30秒ごとにチェック
  }
  
  // フレームレートの監視
  let frameCount = 0;
  let lastTime = performance.now();
  
  function countFrames() {
    frameCount++;
    const currentTime = performance.now();
    
    if (currentTime - lastTime >= 1000) {
      const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
      if (fps < 30) {
        console.warn('Low FPS detected:', fps);
      }
      frameCount = 0;
      lastTime = currentTime;
    }
    
    requestAnimationFrame(countFrames);
  }
  
  requestAnimationFrame(countFrames);
}

// エラーハンドリングの強化
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  showNotification('予期しないエラーが発生しました', 'warning');
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  showNotification('処理中にエラーが発生しました', 'warning');
});

// ページの可視性変更時の処理
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    // ページが非表示になった時の処理
    console.log('Page hidden, pausing animations');
  } else {
    // ページが表示された時の処理
    console.log('Page visible, resuming animations');
  }
});

// リサイズ時の最適化
let resizeTimeout;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    // リサイズ後の処理
    updateSelectionCounter();
  }, 250);
});