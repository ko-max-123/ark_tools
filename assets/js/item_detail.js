const { ipcRenderer } = require('electron');
document.addEventListener('DOMContentLoaded', () => {
    ipcRenderer.on('detail-data', (event, itemId) => {


        // items.jsonからデータを取得
        fetch('assets/json/items.json')
            .then(response => response.json())
            .then(items => {
                console.log("itemId3:", itemId);
                const item = items.find(item => item.itemId === itemId);
                console.log("item:", item);
                console.log("item.name_i18n.ja:", item.name_i18n.ja);


                if (item) {
                    document.getElementById('itemName').textContent = item.name_i18n.ja;
                    //    document.getElementById('item-id').textContent = 'Item ID: ' + itemId;
                    const itemImg = document.getElementById('itemImg');
                    itemImg.width = 100;
                    itemImg.height = 100;
                    itemImg.src = 'img/items/' + itemId + '.png';
                }
            })
            .catch(error => console.error('Error fetching items:', error));

        // stages.jsonからデータを取得
        fetch('assets/json/stages.json')
            .then(response => response.json())
            .then(stages => {
                const foundStages = [];
                for (const stage of stages) {
                    // zoneIdがgachaboxではないステージを抽出
                    if (stage.dropInfos && stage.zoneId !== 'gachabox') {
                        for (const dropInfo of stage.dropInfos) {
                            if (dropInfo.itemId === itemId) {
                                const existingStage = foundStages.find(s => s.stageCode === stage.code_i18n.ja);
                                if (existingStage) {
                                    existingStage.dropTypes.push(dropInfo.dropType);
                                } else {
                                    foundStages.push({
                                        stageCode: stage.code_i18n.ja,
                                        dropTypes: [dropInfo.dropType]
                                    });
                                }
                            }
                        }
                    }
                }

                // 見つけたオブジェクトを表示
                const itemGetStages = document.getElementById('itemGetStages');
                itemGetStages.innerHTML = '';
                foundStages.forEach(stage => {
                    const normalDrop = stage.dropTypes.includes('NORMAL_DROP') ? '<use xlink:href="#check" />' : '';
                    const specialDrop = stage.dropTypes.includes('SPECIAL_DROP') ? '<use xlink:href="#check" />' : '';
                    const extraDrop = stage.dropTypes.includes('EXTRA_DROP') ? '<use xlink:href="#check" />' : '';

                    itemGetStages.innerHTML += `
                        <tr>
                            <th scope="row" class="text-start">${stage.stageCode}</th>
                            <td><svg class="bi" width="24" height="24">${normalDrop}</svg></td>
                            <td><svg class="bi" width="24" height="24">${specialDrop}</svg></td>
                            <td><svg class="bi" width="24" height="24">${extraDrop}</svg></td>
                        </tr>
                    `;
                });
            })
            .catch(error => console.error('Error fetching stages:', error));
    });
});