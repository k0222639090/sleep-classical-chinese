#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_publish_and_generate.py
一次性批量發布 6 篇新文言文篇章，並補足儲備庫未來 15 篇的高品質會考篇目。
"""

import asyncio
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"
DOCS_DIR = BASE_DIR / "docs"
AUDIO_DIR = BASE_DIR / "audio"
WEB_AUDIO_DIR = WEB_DIR / "audio"
DOCS_AUDIO_DIR = DOCS_DIR / "audio"

UPCOMING_FILE = DATA_DIR / "upcoming_corpus.json"
EPISODES_JSON = WEB_DIR / "episodes.json"
DOCS_EPISODES_JSON = DOCS_DIR / "episodes.json"
DATA_EPISODES_JSON = DATA_DIR / "episodes.json"

VOICE_FEMALE = "zh-TW-HsiaoChenNeural"

# 10 篇新補充之國中會考頂級經典儲備篇章
NEW_RESERVE_EPISODES = [
    {
        'id': 'zhuzi_08',
        'title': '《韓非子·難一》自相矛盾',
        'short_title': '自相矛盾',
        'dynasty': '先秦',
        'author': '韓非',
        'category': '諸子哲理與寓言特輯',
        'original_text': '楚人有鬻盾與矛者，譽之曰：「吾盾之堅，物莫能陷也。」又譽其矛曰：「吾矛之利，於物無不陷也。」或曰：「以子之矛陷子之盾，何如？」其人弗能應也。夫不可陷之盾與無不陷之矛，不可同世而立。',
        'annotations': [
            {'term': '鬻', 'note': '音 ㄩˋ (yù)，動詞，販售、賣。'},
            {'term': '譽', 'note': '動詞，稱讚、誇耀。'},
            {'term': '陷', 'note': '動詞，刺破、穿透。'},
            {'term': '或', 'note': '不定代名詞，有人。'},
            {'term': '以', 'note': '介詞，用、拿。'},
            {'term': '何如', 'note': '疑問代詞短語，怎麼樣、會如何。'},
            {'term': '弗', 'note': '否定副詞，不。'},
            {'term': '立', 'note': '動詞，存在、並存。'}
        ],
        'translation': '楚國有一個賣盾牌和長矛的人，他誇獎自己的盾牌說：「我的盾牌非常堅固，任何東西都無法刺穿它。」過了一會兒，他又誇耀自己的長矛說：「我的長矛無比銳利，任何東西沒有刺不穿的。」有人就問他：「如果用你的長矛，去刺你的盾牌，結果會怎麼樣呢？」那個人頓時啞口無言，一句話也回答不上來。世上絕不可能刺穿的盾牌，與無堅不摧的長矛，本來就是不可能同時並存於世上的。',
        'key_points': '★ 成語典故：「自相矛盾」，比喻言語或行事前後不一、互相抵觸。\n★ 會考重點字詞：「鬻」賣也；「陷」穿透也；「或」有人也。\n★ 法家邏輯寓意：韓非子強調言行一致與客觀規律，反對巧言飾非。'
    },
    {
        'id': 'zhuzi_09',
        'title': '《莊子·外物》涸轍之鮒',
        'short_title': '涸轍之鮒',
        'dynasty': '先秦',
        'author': '莊周',
        'category': '諸子哲理與寓言特輯',
        'original_text': '莊周家貧，故往貸粟於監河侯。監河侯曰：「諾。我將得邑金，將貸子三百金，可乎？」莊周忿然作色曰：「周昨來，有中道而呼者。周顧視車轍中，有鮒魚焉。周問之曰：『鮒魚來！子何為者邪？』對曰：『我，東海之波臣也。君豈有斗升之水而活我哉？』周曰：『諾。我且南遊吳越之王，激西江之水而迎子，可乎？』鮒魚忿然作色曰：『吾失我常與，我無所處。吾得斗升之水然活耳，君乃言此，曾不如早索我於枯魚之肆！』」',
        'annotations': [
            {'term': '貸粟', 'note': '借糧食。貸，借入；粟，小米、糧食。'},
            {'term': '監河侯', 'note': '掌管河流灌溉的官員。'},
            {'term': '作色', 'note': '動詞短語，改變臉色，表示生氣。'},
            {'term': '鮒魚', 'note': '鯽魚。車轍中的小魚。'},
            {'term': '波臣', 'note': '水神的臣僕，此為水族自稱。'},
            {'term': '索', 'note': '動詞，尋求、尋找。'},
            {'term': '枯魚之肆', 'note': '肆，店鋪、市場。指乾魚攤子。'}
        ],
        'translation': '莊周家境貧困，因此前往向主管河道的監河侯借糧食。監河侯說：「好啊。等我收到封地的租稅金錢，打算借給你三百兩金子，可以嗎？」莊周生氣地變了臉色說：「我昨天來的時候，半路上聽到有呼救聲。我回頭看車輪壓出的窪槽裡，有一條小鯽魚在那裡。我問牠說：『小鯽魚來，你在這裡做什麼呢？』鯽魚回答：『我是東海的水族臣民。您能否給我一升半斗的水救活我呢？』我說：『好啊。我將要南下遊說吳王和越王，引來西江的水迎請你回大海，可以嗎？』鯽魚氣憤地說：『我失去了平時賴以生存的水環境，已經無處棲身。我只要能得到一升半斗的水就能活下來，您竟然說這種空話，還不如早點到賣魚乾的鋪子裡去找我吧！』」',
        'key_points': '★ 成語典故：「涸轍之鮒」，比喻處於極度困境、急待援救的人。\n★ 會考關鍵句：「曾不如早索我於枯魚之肆」，諷刺遠水救不了近火的虛偽推諉。\n★ 哲理寓意：行善助人貴在即時，切莫空談不切實際的遠大承諾。'
    },
    {
        'id': 'classics_05',
        'title': '《戰國策·楚策》畫蛇添足',
        'short_title': '畫蛇添足',
        'dynasty': '漢代',
        'author': '劉向 編',
        'category': '史記與經典散文特輯',
        'original_text': '楚有祠者，賜其舍人卮酒。舍人相謂曰：「數人飲之不足，一人飲之有餘。請畫地為蛇，先成者飲酒。」一人蛇先成，引酒且飲之，乃左手持卮，右手畫蛇，曰：「吾能為之足。」未成，一人之蛇成，奪其卮曰：「蛇固無足，子安能為之足？」遂飲其酒。為蛇足者，終亡其酒。',
        'annotations': [
            {'term': '祠者', 'note': '主持祭祀的人。'},
            {'term': '舍人', 'note': '門客、隨從貴族的人員。'},
            {'term': '卮', 'note': '音 ㄓ (zhī)，古代的一種盛酒器具。'},
            {'term': '引', 'note': '動詞，拿過來、端起。'},
            {'term': '固', 'note': '副詞，本來、原本。'},
            {'term': '安', 'note': '疑問副詞，怎麼、哪裡。'},
            {'term': '亡', 'note': '音 ㄨㄤˊ (wáng)，動詞，失去、丟失。'}
        ],
        'translation': '楚國有一個主持祭祀的人，賞賜給手下的門客一壺美酒。門客們互相商量說：「幾個人分著喝不夠，一個人喝才綽綽有餘。不如我們在地上畫蛇，誰先畫好，這壺酒就歸誰喝。」其中一個人最先畫好了蛇，他端起酒杯正準備喝，卻看大家都還沒畫完，就左手拿著酒杯，右手接著在地上畫，得意地說：「我還能幫蛇添上腳呢！」他的腳還沒畫完，另一個人的蛇已經畫好了，那人奪過酒壺說：「蛇本來就沒有腳，你怎麼可能替牠添上腳呢？」於是就把那壺酒全喝光了。那個多事給蛇畫腳的人，最終失去了本已到手的美酒。',
        'key_points': '★ 成語典故：「畫蛇添足」，比喻做了多餘的事，反而把事情弄糟、弄巧成拙。\n★ 會考重點字詞：「固」本來；「安」怎麼；「亡」失去；「卮」酒器。\n★ 素養提要：行事應適可而止、恪守本分，切勿畫蛇添足。'
    },
    {
        'id': 'classics_06',
        'title': '《呂氏春秋·察今》刻舟求劍',
        'short_title': '刻舟求劍',
        'dynasty': '先秦',
        'author': '呂不韋 主編',
        'category': '史記與經典散文特輯',
        'original_text': '楚人有涉江者，其劍自舟中墜於水。遽契其舟，曰：「是吾劍之所從墜。」舟止，從其所契者入水求之。舟已行矣，而劍不行，求劍若此，不亦惑乎？以故法為其國與此同。時已徙矣，而法不徙，以此為治，豈不難哉！',
        'annotations': [
            {'term': '涉江', 'note': '渡過江河。涉，渡水。'},
            {'term': '遽', 'note': '音 ㄐㄩˋ (jù)，副詞，急忙、立刻。'},
            {'term': '契', 'note': '音 ㄑㄧˋ (qì)，動詞，用刀雕刻記號。'},
            {'term': '是', 'note': '指示代名詞，此、這裡。'},
            {'term': '求', 'note': '動詞，尋找、搜尋。'},
            {'term': '惑', 'note': '形容詞，糊塗、困惑。'},
            {'term': '徙', 'note': '音 ㄒㄧˇ (xǐ)，動詞，變更、變遷。'}
        ],
        'translation': '楚國有一個乘船渡江的人，他的寶劍不慎從船舷掉落進江水中。他立刻急忙在船身刻下一道記號，說：「這是我寶劍掉落下去的地方。」等到船靠岸停了下來，他便從剛才刻記號的地方跳入水中尋找寶劍。船已經向前行駛了，可是掉進水底的寶劍並沒有隨船移動，像這樣去尋找寶劍，豈不是太糊塗了嗎？用過時陳舊的法規來治理現代的國家，就和這件事情一模一樣。時代已經變遷更替了，法令制度卻不隨之改變，用這種守舊的方法來治理國家，難道不是太艱難了嗎！',
        'key_points': '★ 成語典故：「刻舟求劍」，比喻拘泥成法、不知變通。\n★ 會考重點字詞：「遽」立刻；「契」刻也；「徙」遷徙變更也。\n★ 哲理寓意：世事瞬息萬變，制度與策略必須與時俱進，因時制宜。'
    },
    {
        'id': 'classics_07',
        'title': '《戰國策·燕策》鷸蚌相爭',
        'short_title': '鷸蚌相爭',
        'dynasty': '漢代',
        'author': '劉向 編',
        'category': '史記與經典散文特輯',
        'original_text': '蚌方出曝，而鷸啄其肉，蚌合而箝其喙。鷸曰：「今日不雨，明日不雨，即有死蚌。」蚌亦謂鷸曰：「今日不出，明日不出，即有死鷸。」兩者不肯相舍，漁者得而并禽之。',
        'annotations': [
            {'term': '方', 'note': '副詞，正、剛好。'},
            {'term': '曝', 'note': '音 ㄆㄨˋ (pù)，動詞，曬太陽。'},
            {'term': '箝', 'note': '音 ㄑㄧㄢˊ (qián)，動詞，夾緊、夾住。'},
            {'term': '喙', 'note': '音 ㄏㄨㄟˋ (huì)，名詞，鳥類的嘴。'},
            {'term': '雨', 'note': '音 ㄩˋ (yù)，動詞，下雨。'},
            {'term': '舍', 'note': '通「捨」，動詞，放棄、放開。'},
            {'term': '并', 'note': '副詞，一起、一併。'},
            {'term': '禽', 'note': '通「擒」，動詞，捕捉、擒獲。'}
        ],
        'translation': '有一隻河蚌剛剛從水中爬出灘頭曬太陽，一隻水鳥鷸飛過來啄食牠的肉，河蚌立刻緊緊合上兩扇外殼，夾住了鷸鳥的長嘴。鷸鳥說：「今天不下雨，明天不下雨，江灘上就會有一隻渴死的死蚌。」河蚌也對鷸鳥說：「今天你的嘴拔不出來，明天你的嘴拔不出來，灘頭上就會有一隻餓死的死鷸。」雙方誰都不肯鬆口退讓，正好有個漁夫路過，不費吹灰之力就把牠們兩個一起捉拿帶走了。',
        'key_points': '★ 成語典故：「鷸蚌相爭，漁翁得利」，比喻雙方互不相讓，結果兩敗俱傷，反而讓第三者坐收利益。\n★ 會考通假字：「舍」通「捨」；「禽」通「擒」；「雨」此處名詞作動詞用（下雨）。\n★ 處世智慧：在衝突中若一味固執僵持，最終往往自取滅亡。'
    },
    {
        'id': 'shishuo_13',
        'title': '《世說新語·德行》華歆王朗乘船避難',
        'short_title': '華歆王朗',
        'dynasty': '南朝宋',
        'author': '劉義慶 主編',
        'category': '世說新語名士特輯',
        'original_text': '華歆、王朗俱乘船避難，有一人欲依附，歆輒難之。朗曰：「幸尚寬，何為不可？」後賊追至，王欲舍所攜人。歆曰：「本所以疑，正為此耳。既已納其自託，寧可以急相棄邪？」遂攜拯如初。世以此定華、王之優劣。',
        'annotations': [
            {'term': '俱', 'note': '副詞，一起、同。'},
            {'term': '輒', 'note': '副詞，便、就、立即。'},
            {'term': '難之', 'note': '動詞意動用法，對這件事感到為難或拒絕。'},
            {'term': '幸', 'note': '副詞，幸好、恰好。'},
            {'term': '舍', 'note': '動詞，捨棄、丟下。'},
            {'term': '納', 'note': '動詞，接納、答應。'},
            {'term': '寧', 'note': '副詞，豈、難道。'},
            {'term': '攜拯', 'note': '動詞，帶著並施予救助。'}
        ],
        'translation': '華歆和王朗一同乘船逃難，路上有一個人希望能搭乘他們的船一起逃生，華歆當時便表示猶豫與為難。王朗卻大方地說：「幸好船艙裡還挺寬敞，有什麼不可以的呢？」後來追兵趕到了，王朗急著想把那個隨行搭船的人扔下船不管。華歆這時卻說：「我當初之所以感到猶豫為難，正是預料到可能會有這樣的危急情況。既然剛才已經接納了他的託付，難道可以因為情況危急就把人家拋棄不管了嗎？」於是依然帶著他一同避難到底。世人便以此事來評定華歆與王朗兩人品格德行的優劣。',
        'key_points': '★ 會考名士德行對比：華歆行事審慎、重諾守信；王朗口惠而實不至、臨危自私。\n★ 重點詞義：「難之」為難；「納」接納；「寧」豈、難道。\n★ 素養提要：承諾之前務必審慎深思，一旦答應就要勇於承擔到底。'
    },
    {
        'id': 'shishuo_14',
        'title': '《世說新語·言語》覆巢之下無完卵',
        'short_title': '覆巢無完卵',
        'dynasty': '南朝宋',
        'author': '劉義慶 主編',
        'category': '世說新語名士特輯',
        'original_text': '孔融被收，中外惶怖。時融兒大者九歲，小者八歲，二兒故琢釘戲，了無懼容。融謂使者曰：「冀罪湊於己，二兒可得全不？」兒徐進曰：「大人豈見覆巢之下，復有完卵乎？」尋亦收至。',
        'annotations': [
            {'term': '被收', 'note': '被逮捕收監。被，被動；收，拘捕。'},
            {'term': '中外', 'note': '朝廷內外。'},
            {'term': '琢釘戲', 'note': '古代兒童的一種投擲石子玩遊戲。'},
            {'term': '了無', 'note': '副詞短語，完全沒有。'},
            {'term': '冀', 'note': '動詞，希望。'},
            {'term': '湊', 'note': '動詞，聚集、加於。'},
            {'term': '徐', 'note': '副詞，緩慢、鎮靜地。'},
            {'term': '覆巢', 'note': '傾覆、翻倒的鳥巢。'},
            {'term': '尋', 'note': '時間副詞，不久、隨即。'}
        ],
        'translation': '孔融遭到曹操下令逮捕，朝廷內外一片驚恐慌亂。當時孔融的兩個兒子，大的九歲，小的八歲，兩個孩子依舊平靜地在玩拋釘石的遊戲，臉上絲毫沒有驚慌害怕的神色。孔融不忍心，轉頭對前來逮捕的使者懇求說：「只希望所有的罪過都加在我一人身上，能不能保全這兩個年幼的孩子呢？」這時孩子從容安詳地走上前說：「父親大人，您難道見過翻倒的鳥巢底下，還會有完整不碎的鳥蛋嗎？」果然不久之後，逮捕這兩個孩子的官兵也趕到了。',
        'key_points': '★ 成語典故：「覆巢之下無完卵」，比喻整體一旦傾覆毀滅，其中的個體也絕不可能倖免於難。\n★ 會考重點字詞：「冀」希望；「徐」緩慢從容；「尋」不久。\n★ 人物風骨：展現名士幼子超齡的洞察力、鎮靜臨危不懼之雅量。'
    },
    {
        'id': 'classics_08',
        'title': '《陶淵明·靖節先生集》五柳先生傳',
        'short_title': '五柳先生傳',
        'dynasty': '晉代',
        'author': '陶淵明',
        'category': '史記與經典散文特輯',
        'original_text': '先生不知何許人也，亦不詳其姓字，宅邊有五柳樹，因以為號焉。閑靜少言，不慕榮利。好讀書，不求甚解；每有會意，便欣然忘食。性嗜酒，家貧不能常得。親舊知其如此，或置酒而招之；造飲輒盡，期在必醉。既醉而退，曾不吝情去留。環堵蕭然，不蔽風日；短褐穿結，簞瓢屢空，晏如也。常著文章自娛，頗示己志。忘懷得失，以此自終。',
        'annotations': [
            {'term': '何許人', 'note': '哪裡人。許，處所。'},
            {'term': '不求甚解', 'note': '讀書只領會大意精髓，不咬文嚼字死記硬背。'},
            {'term': '會意', 'note': '領會書中的真意深旨。'},
            {'term': '嗜', 'note': '音 ㄕˋ (shì)，動詞，特別喜好。'},
            {'term': '造飲輒盡', 'note': '造，前往。到那裡喝酒就喝個精光。'},
            {'term': '曾不吝情', 'note': '曾，竟然；吝情，捨不得。毫不拘泥留戀。'},
            {'term': '環堵蕭然', 'note': '堵，矮牆；蕭然，冷清空蕩。形容家徒四壁。'},
            {'term': '短褐穿結', 'note': '粗布短衣破爛打了補丁。'},
            {'term': '晏如', 'note': '安然自得的樣子。'}
        ],
        'translation': '五柳先生不知道是什麼地方的人，也不清楚他的姓名。他家住宅旁邊有五棵柳樹，因此就以此作為自己的稱號。他生性悠閒沈靜，很少說話，不羨慕世俗的榮譽與名利。他特別喜愛讀書，但追求領會書中大意精髓而不鑽牛角尖；每當心靈有所契合體悟，便高興得連吃飯都忘了。他生性酷愛飲酒，但因家境貧困不能經常買酒喝。親戚老友知道他這樣，有時便擺下酒席招待他；他一前去就開懷暢飲直至杯盤見底，唯一的期望就是一定要喝個痛快大醉。喝醉之後就起身告辭告退，對於去留從來毫不拘泥留戀。房屋簡陋家徒四壁，甚至擋不住寒風烈日；身上穿著粗布破爛打了補丁的衣服，盛飯裝水的器具常常空空如也，但他依舊安然自得。他經常寫文章來排遣自娛，充分流露出自己高潔的心志。忘掉世俗名利得失，就這樣泰然自若地過完這樸實的一生。',
        'key_points': '★ 國中會考必考名篇：陶淵明自況之自傳體散文經典。\n★ 核心成語與名句：「不慕榮利」、「不求甚解」、「環堵蕭然」、「晏如也」。\n★ 隱士風骨：呈現安貧樂道、超脫名利、真淳率性的人格境界。'
    },
    {
        'id': 'classics_09',
        'title': '《柳宗元·河東先生集》黔之驢',
        'short_title': '黔之驢',
        'dynasty': '唐代',
        'author': '柳宗元',
        'category': '史記與經典散文特輯',
        'original_text': '黔無驢，有好事者船載以入。至則無可用，放之山下。虎見之，龐然大物也，以為神，蔽林間窺之。稍出近之，慭慭然，莫相知。他日，驢一鳴，虎大駭，遠遁；以為且噬己也，甚恐。然往來視之，覺無異能者；益習其聲，又近出前後，動搖承捷，終不敢搏。稍近益狎，蕩倚衝冒。驢不勝怒，蹄之。虎因喜，計之曰：「技止此耳！」因跳踉大㘎，斷其喉，盡其肉，乃去。',
        'annotations': [
            {'term': '黔', 'note': '貴州一帶的古稱。'},
            {'term': '龐然大物', 'note': '外表巨大魁梧的樣子。'},
            {'term': '蔽', 'note': '動詞，隱蔽、藏匿。'},
            {'term': '慭慭然', 'note': '音 ㄧㄣˋ (yìn)，小心謹慎的樣子。'},
            {'term': '駭', 'note': '動詞，驚嚇、恐懼。'},
            {'term': '遁', 'note': '動詞，逃跑、逃避。'},
            {'term': '噬', 'note': '動詞，咬食、吞噬。'},
            {'term': '狎', 'note': '音 ㄒㄧㄚˊ (xiá)，輕慢、不敬重。'},
            {'term': '蹄之', 'note': '蹄作動詞，用蹄子踢老虎。'},
            {'term': '技止此耳', 'note': '本事不過僅僅如此罷了。止，通「只」。'}
        ],
        'translation': '黔中這個地方原本沒有驢子，有個多事的人用船運了一隻進來。運到之後卻發現沒有什麼用處，就隨手把牠放養在山腳下。老虎看到驢子，見牠身材龐大魁梧，以為是什麼神奇的怪獸，便躲在樹林中暗中窺探牠。後來老虎慢慢走出來接近牠，小心謹慎，不知道牠究竟有多大能耐。有一天，驢子突然長鳴了一聲，老虎大吃一驚，嚇得遠遠逃開；以為驢子即將撲上來咬死自己，心中十分恐懼。然而老虎來回觀察牠，發覺驢子似乎沒有什麼特別的本領；逐漸聽慣了牠的叫聲，又靠近在牠身前身後試探，但始終不敢撲擊。後來老虎漸漸更放肆無禮了，碰撞倚靠衝撞挑釁牠。驢子忍無可忍大為發怒，伸出蹄子踢了老虎一下。老虎因此心中大喜，暗自盤算說：「原來你的本領就只有這一招踢人而已啊！」於是老虎縱身跳躍大吼一聲，猛撲上去咬斷了驢子的喉嚨，吃光了牠的肉，這才心滿意足地離開。',
        'key_points': '★ 成語典故：「黔驢技窮」、「龐然大物」，比喻外表強大但虛有其表、有限的伎倆已經用盡。\n★ 會考重點字詞：「遁」逃跑；「噬」咬；「蹄之」用蹄踢；「技止此耳」本領僅此而已。\n★ 寓意：僅憑龐大外表無以自保，唯有真實能力與智慧才能立足。'
    },
    {
        'id': 'classics_10',
        'title': '《蘇軾·東坡志林》記承天寺夜遊',
        'short_title': '記承天夜遊',
        'dynasty': '宋代',
        'author': '蘇軾',
        'category': '史記與經典散文特輯',
        'original_text': '元豐六年十月十二日夜，解衣欲睡，月色入戶，欣然起行。念無與為樂者，遂至承天寺尋張懷民。懷民亦未寢，相與步於中庭。庭下如積水空明，水中藻荇交橫，蓋竹柏影也。何夜無月？何處無竹柏？但少閑人如吾兩人者耳。',
        'annotations': [
            {'term': '欣然', 'note': '高興、愉悅的樣子。'},
            {'term': '念', 'note': '動詞，想到、考慮到。'},
            {'term': '寢', 'note': '動詞，睡覺。'},
            {'term': '相與', 'note': '副詞，共同、一起。'},
            {'term': '空明', 'note': '清澈透明的樣子。'},
            {'term': '藻荇', 'note': '水草名，此借指竹子與柏樹在月光下的影子。'},
            {'term': '蓋', 'note': '句首發語詞，原來是、大概是。'},
            {'term': '但', 'note': '副詞，只、只是。'},
            {'term': '閑人', 'note': '清閒的人，指具有閒情逸致、超然豁達胸襟的人。'}
        ],
        'translation': '元豐六年十月十二日的夜晚，我脫下外衣正準備入睡，看到皎潔清澈的月光透過門窗灑落進屋內，便高興地穿好衣裳漫步出門。想到沒有可以一同分享這份夜色樂趣的知己，於是走到承天寺尋找張懷民。懷民這時也還沒入睡，我們便一同漫步在寺院的中庭。中庭月光朗照的地面，宛如積聚了一泓澄澈清透明亮的池水，水中彷彿有水草藻荇交錯縱橫，原來那全是竹子和柏樹倒映在地面上的月影啊。哪一個夜晚沒有月亮？哪一個地方沒有青翠的竹柏呢？只是缺少像我們兩個這樣心胸超脫豁達、擁有悠閒情致的雅人罷了。',
        'key_points': '★ 國中會考必考之超高頻名篇：蘇軾貶謫黃州時的性靈小品極致之作。\n★ 神奇譬喻：「庭下如積水空明，水中藻荇交橫，蓋竹柏影也」，以積水喻月色，以水藻喻竹柏之影，空靈澄澈。\n★ 哲理思想：「閑人」一詞自嘲又自得，流露曠達超脫的人生境界與知音相通之樂。'
    }
]

def build_spoken_script(ep):
    """建構適合睡前聆聽的客觀、平穩解說語音劇本"""
    title = ep["title"]
    original = ep["original_text"]
    annotations = ep.get("annotations", [])
    translation = ep["translation"]
    key_points = ep.get("key_points", "")
    
    script = []
    script.append(f"麥麥睡前聽國文。今晚為您解讀的篇章是：{title}。")
    script.append("請放鬆心情，閉上雙眼。我們首先來聆聽原文。")
    script.append(f"【原文】：{original}")
    script.append("接下來，為您逐一梳理本篇的核心字詞與會考必備注釋。")
    
    for idx, item in enumerate(annotations, 1):
        term = item["term"].replace("*", "")
        note = item["note"].replace("*", "")
        script.append(f"第{idx}個關鍵字詞：{term}。意思是：{note}。")
        
    script.append("接下來，是整篇的白話文直譯。請對照體會文言字句的本意。")
    script.append(f"【白話直譯】：{translation}")
    
    if key_points:
        clean_points = key_points.replace("*", "").replace("#", "")
        script.append("最後，為您整理本篇的會考素養提要與核心寓意：")
        script.append(f"{clean_points}")
        
    script.append("今晚的這一篇文言文解讀就到這裡。祝您夜夢甜美，安然入睡。")
    
    text = "\n\n".join(script)
    text = re.sub(r"[#*_~`★]", "", text)
    return text

async def synthesize_one(ep):
    ep_id = ep["id"]
    audio_filename = f"{ep_id}.mp3"
    target_path_1 = AUDIO_DIR / audio_filename
    target_path_2 = WEB_AUDIO_DIR / audio_filename
    target_path_3 = DOCS_AUDIO_DIR / audio_filename
    
    text = build_spoken_script(ep)
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE_FEMALE,
        rate="-10%"
    )
    await communicate.save(str(target_path_1))
    shutil.copyfile(target_path_1, target_path_2)
    shutil.copyfile(target_path_1, target_path_3)
    
    size_kb = target_path_1.stat().st_size / 1024
    print(f"   🎙️ 音檔生成成功 ({size_kb:.1f} KB)：{audio_filename} ({ep['short_title']})")
    
    ep["audio_src"] = f"audio/{audio_filename}"
    ep["publish_date"] = datetime.now().strftime("%Y-%m-%d")

async def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    WEB_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    with open(UPCOMING_FILE, "r", encoding="utf-8") as f:
        upcoming_data = json.load(f)
    with open(EPISODES_JSON, "r", encoding="utf-8") as f:
        published_data = json.load(f)

    published_eps = published_data.get("episodes", [])
    published_ids = {e["id"] for e in published_eps}
    
    upcoming_pool = upcoming_data.get("upcoming_episodes", [])
    
    # 找出尚未發布的前 6 篇
    to_publish = []
    for ep in upcoming_pool:
        if ep["id"] not in published_ids and len(to_publish) < 6:
            to_publish.append(ep)
            
    print(f"🚀 準備批量發布 {len(to_publish)} 篇文言文新篇章：")
    for ep in to_publish:
        print(f" - [{ep['id']}] {ep['title']}")
        
    for ep in to_publish:
        await synthesize_one(ep)
        published_eps.append(ep)
        published_ids.add(ep["id"])

    # 更新已發布 JSON
    published_data["total_episodes"] = len(published_eps)
    published_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(EPISODES_JSON, "w", encoding="utf-8") as f:
        json.dump(published_data, f, ensure_ascii=False, indent=2)
    with open(DOCS_EPISODES_JSON, "w", encoding="utf-8") as f:
        json.dump(published_data, f, ensure_ascii=False, indent=2)
    with open(DATA_EPISODES_JSON, "w", encoding="utf-8") as f:
        json.dump(published_data, f, ensure_ascii=False, indent=2)

    # 擴充 upcoming_corpus.json：包含未發布的原有篇章 + 10 篇新篇章
    remaining_pool = [ep for ep in upcoming_pool if ep["id"] not in published_ids]
    
    existing_reserve_ids = {ep["id"] for ep in remaining_pool}
    for new_ep in NEW_RESERVE_EPISODES:
        if new_ep["id"] not in published_ids and new_ep["id"] not in existing_reserve_ids:
            remaining_pool.append(new_ep)
            
    upcoming_data["upcoming_episodes"] = remaining_pool
    upcoming_data["total_reserves"] = len(remaining_pool)
    upcoming_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(UPCOMING_FILE, "w", encoding="utf-8") as f:
        json.dump(upcoming_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 批量擴充發布完成！")
    print(f"📊 目前已發布總篇數：{len(published_eps)} 篇")
    print(f"📦 未發布儲備庫現存：{len(remaining_pool)} 篇（遠超未來 10 天所需，天天自動解鎖無憂）！")

if __name__ == "__main__":
    asyncio.run(main())
