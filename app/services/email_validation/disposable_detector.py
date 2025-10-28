import asyncio
import httpx
from typing import Set
from app.utils.logger import logger


class DisposableEmailDetector:
    """Detect disposable email addresses"""
    
    def __init__(self):
        self.disposable_domains = set()
        self.last_update = None
        self.update_interval = 24 * 60 * 60  # 24 hours in seconds
        
        # Common disposable email domains (fallback list)
        self.fallback_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'temp-mail.org', 'throwaway.email',
            'getnada.com', 'maildrop.cc', 'sharklasers.com',
            'guerrillamailblock.com', 'pokemail.net', 'spam4.me',
            'bccto.me', 'chacuo.net', 'dispostable.com',
            'mailnesia.com', 'meltmail.com', 'mohmal.com',
            'mytrashmail.com', 'nada.email', 'nada.ltd',
            'nada.pro', 'nada.email', 'nada.ltd', 'nada.pro',
            'tempail.com', 'tempmail.net', 'trashmail.com',
            'trashmail.net', 'trashymail.com', 'trashymail.net',
            'yopmail.com', 'yopmail.net', 'yopmail.org',
            '0-mail.com', '1secmail.com', '20minutemail.com',
            '2prong.com', '30minutemail.com', '3d-painting.com',
            '4warding.com', '5ymail.com', '6ip.us', '7tags.com',
            '9ox.net', 'agedmail.com', 'amilegit.com',
            'anonmails.de', 'antichef.com', 'antichef.net',
            'antireg.ru', 'antispam.de', 'armyspy.com',
            'artman-conception.com', 'auti.st', 'baxomale.ht.cx',
            'beefmilk.com', 'binkmail.com', 'bio-muesli.net',
            'bobmail.info', 'bodhi.lawlita.com', 'bofthew.com',
            'brefmail.com', 'brennendesreich.de', 'bsnow.net',
            'bspamfree.org', 'bugmenot.com', 'bumpymail.com',
            'casualdx.com', 'centermail.com', 'centermail.net',
            'chammy.info', 'childsavings.org', 'chogmail.com',
            'choicemail1.com', 'cool.fr.nf', 'correo.blogos.net',
            'cosmorph.com', 'courriel.fr.nf', 'courrieltemporaire.com',
            'crapmail.org', 'curryworld.de', 'cust.in',
            'dacoolest.com', 'dandikmail.com', 'dayrep.com',
            'dcemail.com', 'deadaddress.com', 'deadspam.com',
            'despam.it', 'despammed.com', 'devnullmail.com',
            'dfgh.net', 'digitalsanctuary.com', 'discardmail.com',
            'discardmail.de', 'disposableaddress.com',
            'disposableemailaddresses.com', 'disposableinbox.com',
            'dispose.it', 'dispostable.com', 'dodgeit.com',
            'dodgit.com', 'dodgit.org', 'donemail.com',
            'dontreg.com', 'dontsendmespam.de', 'dump-email.info',
            'dumpandjunk.com', 'dumpyemail.com', 'e-mail.com',
            'e-mail.org', 'e4ward.com', 'easytrashmail.com',
            'einrot.com', 'email60.com', 'emailias.com',
            'emailinfive.com', 'emailmiser.com', 'emailtemporario.com.br',
            'emailto.de', 'emailwarden.com', 'emailx.at.hm',
            'emailxfer.com', 'emeil.com', 'emeil.in',
            'emz.net', 'enterto.com', 'ephemail.net',
            'etranquil.com', 'etranquil.net', 'etranquil.org',
            'evopo.com', 'explodemail.com', 'fakeinformation.com',
            'fakeinbox.com', 'fakeinbox.net', 'fakeinbox.org',
            'fakemailz.com', 'fastacura.com', 'fastchevy.com',
            'fastchrysler.com', 'fastkawasaki.com', 'fastmazda.com',
            'fastmitsubishi.com', 'fastnissan.com', 'fastsubaru.com',
            'fastsuzuki.com', 'fasttoyota.com', 'fastyamaha.com',
            'filzmail.com', 'fizmail.com', 'fleckens.hu',
            'fr33mail.info', 'frapmail.com', 'front14.org',
            'fux0ringduh.com', 'garliclife.com', 'get1mail.com',
            'get2mail.fr', 'getonemail.com', 'getonemail.net',
            'ghosttexter.com', 'girlsundertheinfluence.com',
            'gotmail.com', 'gotmail.net', 'gotmail.org',
            'great-host.in', 'greensloth.com', 'gsrv.co.uk',
            'guerillamail.biz', 'guerillamail.com', 'guerillamail.de',
            'guerillamail.info', 'guerillamail.net', 'guerillamail.org',
            'guerrillamail.biz', 'guerrillamail.com', 'guerrillamail.de',
            'guerrillamail.info', 'guerrillamail.net', 'guerrillamail.org',
            'h.mintemail.com', 'haltospam.com', 'hatespam.org',
            'hidemail.de', 'hidzz.com', 'hmamail.com',
            'hopemail.biz', 'hotpop.com', 'hulapla.de',
            'ichwann.net', 'ieatspam.eu', 'ieatspam.info',
            'ihateyoualot.info', 'imails.info', 'inboxclean.com',
            'inboxclean.org', 'incognitomail.com', 'incognitomail.net',
            'incognitomail.org', 'insorg-mail.info', 'instant-mail.de',
            'ip6.li', 'irish2me.com', 'iwi.net', 'jetable.com',
            'jetable.fr.nf', 'jetable.net', 'jetable.org',
            'jnxjn.com', 'junk1e.com', 'kaspop.com',
            'keepmymail.com', 'killmail.com', 'killmail.net',
            'kir.ch.tc', 'klassmaster.com', 'klassmaster.net',
            'klzlk.com', 'koszmail.pl', 'kurzepost.de',
            'lawlita.com', 'letthemeatspam.com', 'lhsdv.com',
            'lifebyfood.com', 'link2mail.net', 'litedrop.com',
            'lol.ovpn.to', 'lookugly.com', 'lopl.co.cc',
            'loveable.de', 'lr78.com', 'm4ilweb.info',
            'maboard.com', 'mail-temporaire.fr', 'mail.by',
            'mail.mezimages.net', 'mail2rss.org', 'mail333.com',
            'mail4trash.com', 'mailbidon.com', 'mailbiz.biz',
            'mailblocks.com', 'mailcatch.com', 'maildrop.cc',
            'maileater.com', 'mailexpire.com', 'mailfa.tk',
            'mailforspam.com', 'mailfreeonline.com', 'mailguard.me',
            'mailin8r.com', 'mailinater.com', 'mailinator.com',
            'mailinator.net', 'mailinator.org', 'mailinator2.com',
            'mailincubator.com', 'mailme.lv', 'mailmetrash.com',
            'mailmoat.com', 'mailnesia.com', 'mailnull.com',
            'mailorg.org', 'mailpick.biz', 'mailrock.biz',
            'mailscrap.com', 'mailshell.com', 'mailsiphon.com',
            'mailtemp.info', 'mailtome.de', 'mailtothis.com',
            'mailtrash.net', 'mailtv.tv', 'mailtv.tv',
            'mailzilla.com', 'mailzilla.org', 'makemetheking.com',
            'manybrain.com', 'mbx.cc', 'mciek.com',
            'mega.zik.dj', 'meltmail.com', 'messagebeamer.de',
            'mierdamail.com', 'mintemail.com', 'mjukglass.nu',
            'mobily.com', 'mobily.com', 'moncourrier.fr.nf',
            'monemail.fr.nf', 'monmail.fr.nf', 'mt2009.com',
            'mt2014.com', 'myphantomemail.com', 'myspaceinc.com',
            'myspaceinc.net', 'myspaceinc.org', 'myspacepimpedup.com',
            'myspamless.com', 'mytempemail.com', 'mytempemail.net',
            'mytrashmail.com', 'mytrashmail.compookmail.com',
            'mt2009.com', 'mt2014.com', 'myphantomemail.com',
            'myspaceinc.com', 'myspaceinc.net', 'myspaceinc.org',
            'myspacepimpedup.com', 'myspamless.com', 'mytempemail.com',
            'mytempemail.net', 'mytrashmail.com', 'mytrashmail.compookmail.com',
            'neomailbox.com', 'nepwk.com', 'nervmich.net',
            'nervtmich.net', 'netmails.net', 'netzidiot.de',
            'neverbox.com', 'no-spam.ws', 'nobulk.com',
            'noclickemail.com', 'nogmailspam.info', 'nomail.xl.ci',
            'nomail2me.com', 'nomorespamemails.com', 'nospam.ze.tc',
            'nospam4.us', 'nospamfor.us', 'nospamthanks.info',
            'notmailinator.com', 'nowmymail.com', 'nurfuerspam.de',
            'objectmail.com', 'obobbo.com', 'odnorazovoe.ru',
            'oneoffemail.com', 'onewaymail.com', 'onlatedotcom.info',
            'online.ms', 'opayq.com', 'ordinaryamerican.net',
            'otherinbox.com', 'ovpn.to', 'owlpic.com',
            'pancakemail.com', 'pcusers.otherinbox.com',
            'pepbot.com', 'pfui.ru', 'pimpedupmyspace.com',
            'pjkh.com', 'plexolan.de', 'pookmail.com',
            'privacy.net', 'privy-mail.com', 'privymail.de',
            'proxymail.eu', 'prtnx.com', 'putthisinyourspamdatabase.com',
            'pwrby.com', 'quickinbox.com', 'rcpt.at',
            'recode.me', 'recode.net', 'recode.org',
            'regbypass.com', 'regbypass.comsafe-mail.net',
            'safersignup.de', 'safetymail.info', 'safetypost.de',
            'sandelf.de', 'saynotospams.com', 'selfdestructingmail.com',
            'sendspamhere.com', 'shieldemail.com', 'shieldedmail.com',
            'shieldemail.com', 'shitmail.me', 'shitware.nl',
            'shmeriously.com', 'shortmail.net', 'sibmail.com',
            'sinnlos-mail.de', 'slapsfromlastnight.com', 'slipry.net',
            'slutty.horse', 'sneakemail.com', 'snkmail.com',
            'sofimail.com', 'sofort-mail.de', 'sogetthis.com',
            'soodonims.com', 'spam.la', 'spam.su',
            'spam4.me', 'spamail.de', 'spambob.com',
            'spambob.net', 'spambob.org', 'spambog.com',
            'spambog.de', 'spambog.ru', 'spambox.info',
            'spambox.irishrepublic.uk', 'spambox.us', 'spamcannon.net',
            'spamcero.com', 'spamcon.org', 'spamcorptastic.com',
            'spamcowboy.com', 'spamcowboy.net', 'spamcowboy.org',
            'spamday.com', 'spamex.com', 'spamfighter.cf',
            'spamfighter.ga', 'spamfighter.gq', 'spamfighter.ml',
            'spamfighter.tk', 'spamfree.eu', 'spamfree24.com',
            'spamfree24.de', 'spamfree24.eu', 'spamfree24.net',
            'spamfree24.org', 'spamgoes.com', 'spamherelots.com',
            'spamhereplease.com', 'spamhole.com', 'spamify.com',
            'spaminator.de', 'spamkill.info', 'spaml.com',
            'spaml.de', 'spammotel.com', 'spamobox.com',
            'spamoff.de', 'spamslicer.com', 'spamspot.com',
            'spamthis.co.uk', 'spamthisplease.com', 'spamtrail.com',
            'spamtroll.net', 'spamwc.cf', 'spamwc.ga',
            'spamwc.gq', 'spamwc.ml', 'spamwc.tk',
            'speed.1s.fr', 'spikio.com', 'spoofmail.de',
            'stuffmail.de', 'super-auswahl.de', 'supergreatmail.com',
            'supermailer.jp', 'superrito.com', 'superstachel.de',
            'suremail.info', 'sweetxxx.de', 'teewars.org',
            'teleworm.com', 'teleworm.us', 'temp-mail.org',
            'temp-mail.ru', 'tempail.com', 'tempalias.com',
            'tempe-mail.com', 'tempemail.biz', 'tempemail.com',
            'tempinbox.co.uk', 'tempinbox.com', 'tempmail.eu',
            'tempmail2.com', 'tempmaildemo.com', 'tempmailer.com',
            'tempmailer.de', 'tempomail.fr', 'temporarily.de',
            'temporarioemail.com.br', 'temporaryemail.net',
            'temporaryforwarding.com', 'temporaryinbox.com',
            'temporarymailaddress.com', 'tempthe.net', 'thanksnospam.info',
            'thankyou2010.com', 'thecloudindex.com', 'thisisnotmyrealemail.com',
            'thismail.net', 'throwawayemailaddress.com', 'tilien.com',
            'tittbit.in', 'toomail.biz', 'toomail.com',
            'toomail.net', 'topranklist.de', 'tradermail.info',
            'trash-amil.com', 'trash-mail.at', 'trash-mail.com',
            'trash-mail.de', 'trash2009.com', 'trashemail.de',
            'trashmail.at', 'trashmail.com', 'trashmail.de',
            'trashmail.me', 'trashmail.net', 'trashmail.org',
            'trashymail.com', 'trashymail.net', 'trbvm.com',
            'trbvn.com', 'trbvo.com', 'trialmail.de',
            'trillianpro.com', 'twinmail.de', 'tyldd.com',
            'uggsrock.com', 'umail.net', 'uplipht.com',
            'uroid.com', 'us.af', 'venompen.com',
            'veryrealemail.com', 'viditag.com', 'viewcastmedia.com',
            'viewcastmedia.net', 'viewcastmedia.org', 'vollbio.de',
            'vomoto.com', 'vp.yellowpusher.com', 'vsimcard.com',
            'vubby.com', 'walala.org', 'walkmail.net',
            'webemail.me', 'webm4il.info', 'wegwerfadresse.de',
            'wegwerfemail.de', 'wetrainbayarea.com', 'wetrainbayarea.org',
            'wh4f.org', 'whatiaas.com', 'whatpaas.com',
            'whatsaas.com', 'whopy.com', 'wilemail.com',
            'willselfdestruct.com', 'wuzup.net', 'wuzupmail.net',
            'www.e4ward.com', 'www.gishpuppy.com', 'www.mailinator.com',
            'www.mailinator.net', 'www.mailinator.org', 'wwwnew.eu',
            'x.ip6.li', 'xagloo.com', 'xemaps.com',
            'xents.com', 'xmaily.com', 'xoxy.net',
            'yapped.net', 'yeah.net', 'yopmail.com',
            'yopmail.net', 'yopmail.org', 'ypmail.webarnak.fr.eu.org',
            'yroid.com', 'yspend.com', 'yugas.com',
            'yummyemail.com', 'yupmail.com', 'yupmail.net',
            'yupmail.org', 'zehnminuten.de', 'zehnminutenmail.de',
            'zehnminutenmail.net', 'zehnminutenmail.org', 'zetmail.com',
            'zippymail.info', 'zoemail.net', 'zoemail.org',
            'zomg.info'
        }
    
    async def is_disposable(self, email: str) -> bool:
        """Check if email is from a disposable service"""
        if not email or '@' not in email:
            return False
        
        domain = email.split('@')[1].lower()
        
        # Check if we need to update the list
        await self._update_disposable_list()
        
        return domain in self.disposable_domains
    
    async def _update_disposable_list(self):
        """Update disposable domains list from external source"""
        import time
        
        current_time = time.time()
        
        # Check if we need to update
        if (self.last_update is None or 
            current_time - self.last_update > self.update_interval):
            
            try:
                # Try to fetch from external source
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf"
                    )
                    
                    if response.status_code == 200:
                        domains = set()
                        for line in response.text.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#'):
                                domains.add(line.lower())
                        
                        self.disposable_domains = domains
                        self.last_update = current_time
                        logger.info(f"Updated disposable domains list: {len(domains)} domains")
                        
            except Exception as e:
                logger.warning(f"Failed to update disposable domains list: {e}")
                # Use fallback list if update fails
                if not self.disposable_domains:
                    self.disposable_domains = self.fallback_domains
                    self.last_update = current_time
                    logger.info(f"Using fallback disposable domains list: {len(self.fallback_domains)} domains")
    
    def get_disposable_domains(self) -> Set[str]:
        """Get current list of disposable domains"""
        return self.disposable_domains.copy()


# Global instance
disposable_detector = DisposableEmailDetector()
